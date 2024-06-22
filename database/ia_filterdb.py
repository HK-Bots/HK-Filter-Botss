import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils import get_settings, save_group_settings
from Script import script
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN, FILE_UPDATE_CHANNEL, MOVIE_GROUP_LINK

def clean_file_name(file_name):
    file_name = re.sub(r"\[.*?\]|\{.*?\}|\(.*?\)", "", file_name)
    file_name = file_name.replace("_", " ")
    file_name = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file_name.split()))
    return file_name

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

async def save_file(media, client: Client):
    """Save file in database"""

    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
    try:
        file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
        )
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
        return False, 2
    else:
        try:
            await file.commit()
        except DuplicateKeyError:
            logger.warning(
                f'{getattr(media, "file_name", "NO_FILE")} is already saved in database'
            )
            return False, 0
        else:
            logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
            return True, 1

    file_name = clean_file_name(media.file_name)
    match = re.search(r"^(.+?)[\s\.-](\d{4})", file_name, re.IGNORECASE)
    movie_name = match.group(1) if match else file_name
    processed_movie = await db[COLLECTION_NAME].find_one({"movie_name": {"$regex": movie_name, "$options": "i"}})
    if processed_movie:
        print(f'{movie_name} has already been processed')
        return 'dup'
    await db[COLLECTION_NAME].insert_one({"movie_name": movie_name})
    year = match.group(2) if match else "Unknown Year"
    size = f"{media.file_size / 1048576:.2f} MB" if media.file_size < 1073741824 else f"{media.file_size / 1073741824:.2f} GB"
    buttons = [[
        InlineKeyboardButton('🔍 Search this movie here', url=MOVIE_GROUP_LINK)
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await client.send_message(
        chat_id=FILE_UPDATE_CHANNEL,
        text=script.INDEX_FILE_TXT.format(movie_name, year, size),  # Modify as per required format
        reply_markup=reply_markup
    )
    return 'suc'

async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset)"""
    if chat_id is not None:
        settings = await get_settings(int(chat_id))
        try:
            max_results = 10 if settings.get('max_btn') else int(MAX_B_TN)
        except KeyError:
            await save_group_settings(int(chat_id), 'max_btn', False)
            settings = await get_settings(int(chat_id))
            max_results = 10 if settings.get('max_btn') else int(MAX_B_TN)

    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error:
        return []

    filter = {'$or': [{'file_name': regex}, {'caption': regex}]} if USE_CAPTION_FILTER else {'file_name': regex}
    if file_type:
        filter['file_type'] = file_type

    total_results = await Media.count_documents(filter)
    next_offset = offset + max_results if offset + max_results <= total_results else ''

    cursor = Media.find(filter).sort('$natural', -1).skip(offset).limit(max_results)
    files = await cursor.to_list(length=max_results)

    return files, next_offset, total_results

async def get_bad_files(query, file_type=None, filter=False):
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error:
        return []

    filter = {'$or': [{'file_name': regex}, {'caption': regex}]} if USE_CAPTION_FILTER else {'file_name': regex}
    if file_type:
        filter['file_type'] = file_type

    total_results = await Media.count_documents(filter)
    cursor = Media.find(filter).sort('$natural', -1)
    files = await cursor.to_list(length=total_results)

    return files, total_results

async def get_file_details(query):
    filter = {'file_id': query}
    cursor = Media.find(filter)
    filedetails = await cursor.to_list(length=1)
    return filedetails

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref

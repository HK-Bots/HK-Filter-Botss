import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN
from utils import get_settings, save_group_settings
from info *    

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

    # TODO: Find better way to get same file_id for same media to avoid duplicates
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
            print(f'{file_name} is already saved in database') 
            return 'dup'
        else:
            print(f'{file_name} is saved to database')

          #Nothing Much Brother
            movie_name = clean_file_name(media.file_name)            
            year = extract_year(media.file_name)
            language = extract_language(media.file_name)            
            if media.file_size < 1073741824:
                size = f"{media.file_size / 1048576:.2f} MB"
            else:
                size = f"{media.file_size / 1073741824:.2f} GB"
            buttons = [[
            InlineKeyboardButton('🔍 ꜱᴇᴀʀᴄʜ ᴛʜɪꜱ ᴍᴏᴠɪᴇ ʜᴇʀᴇ', url=MOVIE_GROUP_LINK)
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.send_message(
                chat_id=LOG_CHANNEL,
                text=script.INDEX_FILE_TXT.format(movie_name, year, language, size),
                reply_markup=reply_markup)
            return 'suc' 

#Add This Code In Your Repo

def extract_year(file_name):
    """Extracts the year from the file name."""
    match = re.search(r'\b(19\d{2}|20\d{2})\b', file_name)
    if match:
        return match.group(1)
    return None

def extract_language(file_name):
    """Extracts the language from the file name."""
    # Add language patterns you want to extract
    language_patterns = [
        r'\b(Hindi|English|Tamil|Telugu|Malayalam|Kannada)\b',
        # Add more language patterns as needed
    ]
    for pattern in language_patterns:
        match = re.search(pattern, file_name, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def clean_file_name(file_name):
    file_name = re.sub(r"\[.*?\]|\{.*?\}|\(.*?\)", "", file_name)
    file_name = file_name.rsplit('.', 1)[0]
    file_name = file_name.replace("_", " ")
    file_name = file_name.replace('#', '')
    file_name = file_name.replace('×', '')
    file_name = re.sub(r'\b\d{4}\b', '', file_name)
    language_codes = ['english', 'hindi', 'kannada', 'malayalam', 'tamil', 'telugu', 'bengali', 
                       'marathi', 'gujarati', 'punjabi', 'urdu', 'french', 'spanish', 'german',
                       'japanese', 'korean', 'chinese', 'russian', 'arabic', 'portuguese']
    file_name = ' '.join(filter(
    lambda x: not x.startswith(('[', '@', 'www.'))
              and not x.lower() in [
                  '1080p', '2160p', '4k', '5k', '8k', '1440p', '2k', '480p', '360p', '720p', 
                  'hd', 'fhd', 'qhd', 'uhd', 'sd', 'hdtv', 'webrip', 'bluray', 'blu-ray', 'brrip',
                  'h264', 'h.264', 'h265', 'h.265', 'x264', 'x.264', 'x265', 'x.265', 'hevc', 
                  'aac', 'ac3', 'dts', 'dts-hd', 'mp3', 'flac', 'opus', 
                  'web-dl', 'webdl', 'dvdrip', 'dvd-rip', 'xvid', 'divx', 
                  'hdr', 'hdr10', 'hdr10+', 'dolby vision', 'dv',
                  'hdrip', 'hdts', 'camrip', 'cam', 'telesync', 'ts', 'tc',
                  'esubs', 'esub', 'subtitles', 'subs',
                  'avc', 'truehd', 'atmos', 'dd5.1', 'dd7.1',
                  'hq', 'remastered', 'extended', 'unrated', 'director\'s cut', 
                  'remux', 'encode', 'multi', 'dual audio', 'multi-audio',
                  'predvd', 'pre-dvd', 'screener'
              ]
              and not x.lower() in language_codes
              and not x.lower().startswith(('x2', 'x'))
              and not x.isdigit(),  # Remove standalone numbers 
    file_name.split()
    ))
    file_name = re.sub(r'[^\w\s]', '', file_name)
    file_name = ' '.join(file_name.split())
    return file_name



async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset)"""
    if chat_id is not None:
        settings = await get_settings(int(chat_id))
        try:
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)
        except KeyError:
            await save_group_settings(int(chat_id), 'max_btn', False)
            settings = await get_settings(int(chat_id))
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)
    query = query.strip()
    #if filter:
        #better ?
        #query = query.replace(' ', r'(\s|\.|\+|\-|_)')
        #raw_pattern = r'(\s|_|\-|\.|\+)' + query + r'(\s|_|\-|\.|\+)'
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    total_results = await Media.count_documents(filter)
    next_offset = offset + max_results

    if next_offset > total_results:
        next_offset = ''

    cursor = Media.find(filter)
    # Sort by recent
    cursor.sort('$natural', -1)
    # Slice files according to offset and max results
    cursor.skip(offset).limit(max_results)
    # Get list of files
    files = await cursor.to_list(length=max_results)

    return files, next_offset, total_results

async def get_bad_files(query, file_type=None, filter=False):
    """For given query return (results, next_offset)"""
    query = query.strip()
    #if filter:
        #better ?
        #query = query.replace(' ', r'(\s|\.|\+|\-|_)')
        #raw_pattern = r'(\s|_|\-|\.|\+)' + query + r'(\s|_|\-|\.|\+)'
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    total_results = await Media.count_documents(filter)

    cursor = Media.find(filter)
    # Sort by recent
    cursor.sort('$natural', -1)
    # Get list of files
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

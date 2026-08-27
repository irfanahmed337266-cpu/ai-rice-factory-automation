from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks
)

from fastapi.responses import FileResponse
from pydantic import BaseModel

import speech_recognition as sr
import edge_tts
import tempfile
import os
import json

from google import genai

from app.database import SessionLocal

from app.ai_actions import (
    create_purchase_action,
    create_sale_action
)

from app.routers.ai import (
    generate_ai_reply,
    clean_json_response,
    safe_float,
    safe_int
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/voice",
    tags=["Voice AI"]
)


# ============================================================
# GEMINI
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured in the .env file."
    )

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# VOICE MEMORY
# ============================================================

voice_purchase_memory = {}
voice_sale_memory = {}


# ============================================================
# VOICE ROUTING
# ============================================================

def detect_voice_intent(text: str) -> str:

    prompt = f"""
You are a routing system for a Rice Factory AI Assistant.

The user spoke this sentence:

{text}

Determine the user's intent.

Possible intents:

purchase
sale
chat

Rules:

- If the user wants to buy/purchase/procure material from a supplier,
  return "purchase".
- If the user wants to sell/sale product to a buyer/customer,
  return "sale".
- If the user is asking a business question such as sales, profit,
  stock, expenses, receivables, payables, etc., return "chat".
- If unclear, return "chat".

Return ONLY one word:

purchase

OR

sale

OR

chat
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        intent = response.text.strip().lower()

        if "purchase" in intent:
            return "purchase"

        if "sale" in intent:
            return "sale"

        return "chat"

    except Exception:

        # ----------------------------------------------------
        # Fallback keyword detection
        # ----------------------------------------------------

        text_lower = text.lower()

        purchase_words = [
            "purchase",
            "buy",
            "buying",
            "supplier",
            "kharid",
            "khareed",
            "khareedna",
            "purchase kar",
            "پرچیز",
            "خرید",
            "سپلائر"
        ]

        sale_words = [
            "sale",
            "sell",
            "selling",
            "buyer",
            "customer",
            "bech",
            "bechna",
            "فروخت",
            "فروخت کرنا",
            "خریدار",
            "کسٹمر"
        ]

        if any(word in text_lower for word in purchase_words):
            return "purchase"

        if any(word in text_lower for word in sale_words):
            return "sale"

        return "chat"


# ============================================================
# EXTRACT PURCHASE DATA
# ============================================================

def extract_purchase_data(
    text: str,
    memory: dict
):

    prompt = f"""
You are a Rice Factory Purchase Assistant.

Extract purchase information from the user's message.

Previous information:

{json.dumps(memory, ensure_ascii=False)}

Current message:

{text}

Return ONLY valid JSON.

Required fields:

supplier_name
material_name
quantity
purchase_rate
transport_cost
notes

Rules:

1. Keep valid previous information.
2. Replace previous information if user corrects it.
3. Do not invent information.
4. Missing fields must be null.
5. Numbers must be numbers.

Example:

{{
    "supplier_name": "Al-Rehman Rice Supplier",
    "material_name": "Phak",
    "quantity": 10,
    "purchase_rate": 250,
    "transport_cost": 500,
    "notes": null
}}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    clean_text = clean_json_response(
        response.text
    )

    data = json.loads(
        clean_text
    )

    if not isinstance(data, dict):
        raise ValueError(
            "Invalid purchase extraction."
        )

    return data


# ============================================================
# PROCESS PURCHASE
# ============================================================

def process_voice_purchase(
    text: str,
    db,
    session_id: str = "voice-default"
):

    memory = voice_purchase_memory.get(
        session_id,
        {}
    )

    try:

        data = extract_purchase_data(
            text,
            memory
        )

    except Exception:

        return {
            "success": False,
            "message": (
                "Purchase کی معلومات سمجھ نہیں آئیں۔ "
                "براہ کرم دوبارہ واضح کریں۔"
            )
        }

    fields = [
        "supplier_name",
        "material_name",
        "quantity",
        "purchase_rate",
        "transport_cost",
        "notes"
    ]

    # --------------------------------------------------------
    # UPDATE MEMORY
    # --------------------------------------------------------

    for key in fields:

        value = data.get(key)

        if value is not None:

            if isinstance(value, str):

                value = value.strip()

                if not value:
                    continue

            memory[key] = value

    voice_purchase_memory[session_id] = memory

    # --------------------------------------------------------
    # SUPPLIER
    # --------------------------------------------------------

    if not memory.get("supplier_name"):

        return {
            "success": False,
            "status": "waiting_for_supplier",
            "message": "کس supplier سے purchase کرنی ہے؟"
        }

    # --------------------------------------------------------
    # MATERIAL
    # --------------------------------------------------------

    if not memory.get("material_name"):

        return {
            "success": False,
            "status": "waiting_for_material",
            "message": "کون سا material purchase کرنا ہے؟"
        }

    # --------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------

    quantity = safe_int(
        memory.get("quantity")
    )

    if quantity is None or quantity <= 0:

        return {
            "success": False,
            "status": "waiting_for_quantity",
            "message": "کتنی مقدار purchase کرنی ہے؟"
        }

    # --------------------------------------------------------
    # PURCHASE RATE
    # --------------------------------------------------------

    purchase_rate = safe_float(
        memory.get("purchase_rate")
    )

    if purchase_rate is not None and purchase_rate < 0:

        return {
            "success": False,
            "status": "invalid_purchase_rate",
            "message": "Purchase rate درست درج کریں۔"
        }

    # --------------------------------------------------------
    # TRANSPORT
    # --------------------------------------------------------

    transport_cost = safe_float(
        memory.get("transport_cost"),
        default=0
    )

    if transport_cost < 0:

        return {
            "success": False,
            "status": "invalid_transport_cost",
            "message": "Transport cost درست درج کریں۔"
        }

    # --------------------------------------------------------
    # CREATE PURCHASE
    # --------------------------------------------------------

    result = create_purchase_action(

        db=db,

        supplier_name=memory["supplier_name"],

        material_name=memory["material_name"],

        quantity=quantity,

        purchase_rate=purchase_rate,

        transport_cost=transport_cost,

        notes=memory.get("notes")
    )

    # --------------------------------------------------------
    # CLEAR MEMORY
    # --------------------------------------------------------

    if result.get("success"):

        voice_purchase_memory.pop(
            session_id,
            None
        )

    return result


# ============================================================
# EXTRACT SALE DATA
# ============================================================

def extract_sale_data(
    text: str,
    memory: dict
):

    prompt = f"""
You are a Rice Factory Sales Assistant.

Extract sales information from the user's message.

Previous information:

{json.dumps(memory, ensure_ascii=False)}

Current message:

{text}

Return ONLY valid JSON.

Required fields:

buyer_name
product_name
quantity
selling_rate
transport_cost
notes

Rules:

1. Keep valid previous information.
2. Replace previous information if user corrects it.
3. Do not invent information.
4. Missing fields must be null.
5. Numbers must be numbers.

Example:

{{
    "buyer_name": "ABC Rice Mills",
    "product_name": "Phak Rice",
    "quantity": 5,
    "selling_rate": 300,
    "transport_cost": 100,
    "notes": null
}}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    clean_text = clean_json_response(
        response.text
    )

    data = json.loads(
        clean_text
    )

    if not isinstance(data, dict):
        raise ValueError(
            "Invalid sale extraction."
        )

    return data


# ============================================================
# PROCESS SALE
# ============================================================

def process_voice_sale(
    text: str,
    db,
    session_id: str = "voice-default"
):

    memory = voice_sale_memory.get(
        session_id,
        {}
    )

    try:

        data = extract_sale_data(
            text,
            memory
        )

    except Exception:

        return {
            "success": False,
            "message": (
                "Sale کی معلومات سمجھ نہیں آئیں۔ "
                "براہ کرم دوبارہ واضح کریں۔"
            )
        }

    fields = [
        "buyer_name",
        "product_name",
        "quantity",
        "selling_rate",
        "transport_cost",
        "notes"
    ]

    # --------------------------------------------------------
    # UPDATE MEMORY
    # --------------------------------------------------------

    for key in fields:

        value = data.get(key)

        if value is not None:

            if isinstance(value, str):

                value = value.strip()

                if not value:
                    continue

            memory[key] = value

    voice_sale_memory[session_id] = memory

    # --------------------------------------------------------
    # BUYER
    # --------------------------------------------------------

    if not memory.get("buyer_name"):

        return {
            "success": False,
            "status": "waiting_for_buyer",
            "message": "کس buyer کو sale کرنی ہے؟"
        }

    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    if not memory.get("product_name"):

        return {
            "success": False,
            "status": "waiting_for_product",
            "message": "کون سا product فروخت کرنا ہے؟"
        }

    # --------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------

    quantity = safe_int(
        memory.get("quantity")
    )

    if quantity is None or quantity <= 0:

        return {
            "success": False,
            "status": "waiting_for_quantity",
            "message": "کتنی مقدار فروخت کرنی ہے؟"
        }

    # --------------------------------------------------------
    # SELLING RATE
    # --------------------------------------------------------

    selling_rate = safe_float(
        memory.get("selling_rate")
    )

    if selling_rate is None or selling_rate <= 0:

        return {
            "success": False,
            "status": "waiting_for_selling_rate",
            "message": "Selling rate کیا ہے؟"
        }

    # --------------------------------------------------------
    # TRANSPORT
    # --------------------------------------------------------

    transport_cost = safe_float(
        memory.get("transport_cost"),
        default=0
    )

    if transport_cost < 0:

        return {
            "success": False,
            "status": "invalid_transport_cost",
            "message": "Transport cost درست درج کریں۔"
        }

    # --------------------------------------------------------
    # CREATE SALE
    # --------------------------------------------------------

    result = create_sale_action(

        db=db,

        buyer_name=memory["buyer_name"],

        product_name=memory["product_name"],

        quantity=quantity,

        selling_rate=selling_rate,

        transport_cost=transport_cost,

        notes=memory.get("notes")
    )

    # --------------------------------------------------------
    # CLEAR MEMORY
    # --------------------------------------------------------

    if result.get("success"):

        voice_sale_memory.pop(
            session_id,
            None
        )

    return result


# ============================================================
# VOICE TO TEXT
# ============================================================

@router.post("/audio")
def voice_audio(
    file: UploadFile = File(...)
):

    allowed_types = [
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3"
    ]

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail="Please upload a WAV or MP3 audio file."
        )

    suffix = ".wav"

    if file.filename:
        if file.filename.lower().endswith(".mp3"):
            suffix = ".mp3"

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    )

    try:

        temp_file.write(
            file.file.read()
        )

        temp_file.close()

        recognizer = sr.Recognizer()

        with sr.AudioFile(
            temp_file.name
        ) as source:

            audio = recognizer.record(
                source
            )

        try:

            text = recognizer.recognize_google(
                audio,
                language="ur-PK"
            )

        except sr.UnknownValueError:

            raise HTTPException(
                status_code=400,
                detail="Audio could not be understood."
            )

        except sr.RequestError as e:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Speech recognition service error: "
                    f"{str(e)}"
                )
            )

        return {
            "success": True,
            "filename": file.filename,
            "text": text
        }

    finally:

        if os.path.exists(
            temp_file.name
        ):

            os.remove(
                temp_file.name
            )


# ============================================================
# TEXT TO SPEECH REQUEST
# ============================================================

class SpeakRequest(BaseModel):

    text: str


# ============================================================
# EDGE TTS
# ============================================================

async def generate_voice(
    text: str,
    output_file: str
):

    voice = "ur-PK-UzmaNeural"

    communicate = edge_tts.Communicate(
        text,
        voice
    )

    await communicate.save(
        output_file
    )


# ============================================================
# TEXT TO SPEECH
# ============================================================

@router.post("/speak")
async def voice_speak(
    request: SpeakRequest,
    background_tasks: BackgroundTasks
):

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp3"
    )

    temp_file.close()

    try:

        await generate_voice(
            request.text,
            temp_file.name
        )

        background_tasks.add_task(
            os.remove,
            temp_file.name
        )

        return FileResponse(
            temp_file.name,
            media_type="audio/mpeg",
            filename="speech.mp3"
        )

    except Exception as e:

        if os.path.exists(
            temp_file.name
        ):

            os.remove(
                temp_file.name
            )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Text-to-speech error: {str(e)}"
            )
        )


# ============================================================
# COMPLETE VOICE AI ASSISTANT
# ============================================================

@router.post("/assistant")
async def voice_assistant(
    file: UploadFile = File(...)
):

    allowed_types = [
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3"
    ]

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail="Please upload a WAV or MP3 audio file."
        )

    # --------------------------------------------------------
    # SAVE INPUT
    # --------------------------------------------------------

    suffix = ".wav"

    if file.filename:

        if file.filename.lower().endswith(".mp3"):
            suffix = ".mp3"

    temp_audio = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    )

    output_audio = None

    try:

        temp_audio.write(
            file.file.read()
        )

        temp_audio.close()

        # ----------------------------------------------------
        # SPEECH TO TEXT
        # ----------------------------------------------------

        recognizer = sr.Recognizer()

        with sr.AudioFile(
            temp_audio.name
        ) as source:

            audio = recognizer.record(
                source
            )

        try:

            text = recognizer.recognize_google(
                audio,
                language="ur-PK"
            )

        except sr.UnknownValueError:

            raise HTTPException(
                status_code=400,
                detail="Audio could not be understood."
            )

        except sr.RequestError as e:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Speech recognition service error: "
                    f"{str(e)}"
                )
            )

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        db = SessionLocal()

        try:

            # ------------------------------------------------
            # DETECT INTENT
            # ------------------------------------------------

            intent = detect_voice_intent(
                text
            )

            # ------------------------------------------------
            # PURCHASE
            # ------------------------------------------------

            if intent == "purchase":

                result = process_voice_purchase(
                    text=text,
                    db=db,
                    session_id="voice-default"
                )

                if result.get("success"):

                    reply = result.get(
                        "message",
                        "Purchase کامیابی سے درج کر دی گئی ہے۔"
                    )

                else:

                    reply = result.get(
                        "message",
                        "Purchase مکمل نہیں ہو سکی۔"
                    )

            # ------------------------------------------------
            # SALE
            # ------------------------------------------------

            elif intent == "sale":

                result = process_voice_sale(
                    text=text,
                    db=db,
                    session_id="voice-default"
                )

                if result.get("success"):

                    reply = result.get(
                        "message",
                        "Sale کامیابی سے درج کر دی گئی ہے۔"
                    )

                else:

                    reply = result.get(
                        "message",
                        "Sale مکمل نہیں ہو سکی۔"
                    )

            # ------------------------------------------------
            # NORMAL AI CHAT
            # ------------------------------------------------

            else:

                reply = generate_ai_reply(
                    message=text,
                    db=db
                )

        finally:

            db.close()

        # ----------------------------------------------------
        # EDGE TTS
        # ----------------------------------------------------

        output_audio = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        )

        output_audio.close()

        try:

            await generate_voice(
                reply,
                output_audio.name
            )

        except Exception as e:

            if os.path.exists(
                output_audio.name
            ):

                os.remove(
                    output_audio.name
                )

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Text-to-speech error: {str(e)}"
                )
            )

        # ----------------------------------------------------
        # DELETE INPUT AUDIO
        # ----------------------------------------------------

        if os.path.exists(
            temp_audio.name
        ):

            os.remove(
                temp_audio.name
            )

        # ----------------------------------------------------
        # RETURN AI VOICE
        # ----------------------------------------------------

        return FileResponse(
            output_audio.name,
            media_type="audio/mpeg",
            filename="ai_reply.mp3"
        )

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Voice assistant error: {str(e)}"
            )
        )

    finally:

        if os.path.exists(
            temp_audio.name
        ):

            os.remove(
                temp_audio.name
            )
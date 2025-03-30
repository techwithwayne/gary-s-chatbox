from django.shortcuts import render
from django.http import JsonResponse
from openai import OpenAI
from dotenv import load_dotenv
from .models import StoreInfo, ConversationLog
import os
import traceback

from django.core.mail import send_mail
from django.conf import settings

# Load environment variables from .env
load_dotenv()

# Set up OpenAI client with your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Renders the chat UI page
def chatbot_home(request):
    return render(request, 'chatbot/chatbot.html')

# Handles chatbot interaction via AJAX POST
def ask_bot(request):
    if request.method == "POST":
        user_message = request.POST.get("message")
        if not user_message:
            return JsonResponse({'error': 'No message received'}, status=400)

        try:
            # Pull the store info from the database
            store_info = StoreInfo.objects.first()
            if not store_info:
                return JsonResponse({'error': 'Store information is missing. Please add it via admin.'}, status=500)

            services_text = store_info.services.strip()

            # Build the system prompt dynamically from DB content
            system_prompt = (
                "You are a helpful, friendly assistant for Gary’s Foods, a grocery store in Mount Vernon, Iowa. "
                "Here is important information about the store you must use when answering questions:\n\n"
                f"- Store Hours: {store_info.hours}\n"
                f"- Phone: {store_info.phone}\n"
                f"- Address: {store_info.address}\n"
                f"- Services: {services_text}\n"
                f"- Weekly Flyer: {store_info.flyer_url}\n\n"
                "Always be concise, helpful, and polite. If you're unsure of something, suggest calling the store."
            )

            # Call OpenAI to get bot response
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )

            bot_reply = response.choices[0].message.content.strip()
            
            should_render_as_html = False  # default
            
            if "where are you located" in user_message.lower() or "location" in user_message.lower():
                encoded_address = store_info.address.replace(" ", "+")
                gmaps_url = f"https://www.google.com/maps?q={encoded_address}"
                embed_code = (
                    f"<p>You can find us at {store_info.address}.</p>"
                    f"<iframe src='{gmaps_url}&output=embed' width='100%' height='200' "
                    f"style='border:0; border-radius:10px; margin-top:10px;' allowfullscreen='' "
                    f"loading='lazy' referrerpolicy='no-referrer-when-downgrade'></iframe>"
                )

                bot_reply = embed_code
                should_render_as_html = True

            # ESCALATION LOGIC
            trigger_keywords = ["talk to someone", "real person", "human", "manager", "escalate", "complaint"]
            should_escalate = any(word in user_message.lower() for word in trigger_keywords) or \
                  any(word in bot_reply.lower() for word in trigger_keywords)

            if should_escalate:
                bot_reply = (
                    "I'm happy to connect you with someone who can help! "
                    f"You can call the store directly at {store_info.phone} "
                    f"or visit us in person at {store_info.address}."
                )

                send_mail(
                    subject="⚠️ Chatbot Escalation Triggered",
                    message=(
                        f"A user may need help from a human.\n\n"
                        f"User Message: {user_message}\n"
                        f"Bot Reply: {bot_reply}\n"
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=settings.ESCALATION_EMAIL_TO,
                    fail_silently=False,
                )

            # Log the conversation
            ConversationLog.objects.create(
                user_message=user_message,
                bot_reply=bot_reply
            )

            return JsonResponse({
                'reply': bot_reply,
                'render_as_html': should_render_as_html
                })

        except Exception as e:
            print("EXCEPTION:", str(e))
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

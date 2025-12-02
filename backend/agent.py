import logging
import json
import asyncio
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins.openai.realtime import RealtimeModel
from dotenv import load_dotenv
from api import AssistantFnc
from prompts import WELCOME_MESSAGE, INSTRUCTIONS

load_dotenv()
logger = logging.getLogger("agent")

# Entrypoint for the agent worker
async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting to {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    await ctx.wait_for_participant()

    model = RealtimeModel(
        instructions=INSTRUCTIONS,
        voice="shimmer",
        temperature=0.8,
        modalities=["audio", "text"]
    )

# Initialize Agent with Tool Functionality and connect to Room
    fnc = AssistantFnc()
    agent = MultimodalAgent(model=model, fnc_ctx=fnc)
    agent.start(ctx.room)

# Choosing the first session for interaction from the realtime model
    session = model.sessions[0]
    session.conversation.item.create(llm.ChatMessage(role="assistant", content=WELCOME_MESSAGE))
    session.response.create()

# Handle incoming image data from clients
    @ctx.room.on("data_received")
    def on_data(payload):
        # Handle image-share topic brutal way because model halucination
        if payload.topic == "image-share":
            try:
                data = json.loads(payload.data.decode("utf-8"))
                analysis = data.get("analysis", "")

                fnc.set_photo_analysis(analysis)
                # Should be awaited but callback can't be async, so could be as a background job if needed
                fnc.save_image_url(data.get("url"))

                prompt = (
                    f"SYSTEM: New image uploaded. ANALYSIS:\n{analysis}\n"
                    "INSTRUCTION: Answer user questions based on this. "
                    "Do NOT summarize this in tool calls; system does it automatically."
                )
                session.conversation.item.create(llm.ChatMessage(role="system", content=prompt))
                session.response.create()
            except Exception as e:
                logger.error(f"Data error: {e}")

    # Keep alive
    await ctx.room.disconnect_future


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
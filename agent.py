import os
import json
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

# 1. تحميل المتغيرات السرية من ملف .env
load_dotenv()
notion_key = os.getenv("NOTION_API_KEY")

async def main():
    print("🔌 Initializing Notion MCP Server & AI Agent...")

    # 2. تجهيز الهيدرز المطلوبة خصيصاً لحزمة Notion الرسمية عبر OpenAPI
    env_vars = os.environ.copy()
    if notion_key:
        # حزمة Notion الحديثة تتطلب الـ Authorization و Notion-Version داخل OPENAPI_MCP_HEADERS
        headers_dict = {
            "Authorization": f"Bearer {notion_key}",
            "Notion-Version": "2022-06-28"
        }
        env_vars["OPENAPI_MCP_HEADERS"] = json.dumps(headers_dict)

    # 3. تشغيل حزمة Notion MCP الرسمية الصحيحة عبر npx
    async with MCPServerStdio(
        params={
            "command": "npx",
            "args": ["-y", "@notionhq/notion-mcp-server"],
            "env": env_vars
        }
    ) as notion_server:

        # 4. قراءة ملف الإرشادات لو وجد، أو استخدام إرشاد افتراضي
        agent_instructions = "You are a professional assistant. Search my Notion workspace before answering."
        if os.path.exists("instructions.md"):
            with open("instructions.md", "r", encoding="utf-8") as f:
                agent_instructions = f.read()

        # 5. بناء الوكيل الذكي (Agent)
        notion_agent = Agent(
            name="Notion Content Assistant",
            model="gpt-4o",
            instructions=agent_instructions,
            mcp_servers=[notion_server]
        )

        print("\n✅ Notion Agent is ready! Type 'exit' or 'quit' to end.\n")
        print("-" * 50)

        # 6. حلقة المحادثة التفاعلية
        input_items = []
        while True:
            try:
                user_input = input("\n💬 You: ")
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("👋 Goodbye!")
                    break
                
                if not user_input.strip():
                    continue

                input_items.append({"role": "user", "content": user_input})

                print("🤖 Agent is thinking & checking Notion... ", end="", flush=True)

                result = await Runner.run(notion_agent, input_items)
                
                print(f"\n🤖 Agent: {result.final_output}")
                
                input_items.append({"role": "assistant", "content": result.final_output})

            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                break
            except Exception as e:
                print(f"\n❌ Error during conversation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
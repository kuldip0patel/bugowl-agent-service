from dotenv import load_dotenv

from browser_use import Agent
from browser_use.llm import ChatGoogle

load_dotenv()
import asyncio

llm = ChatGoogle(model='gemini-2.5-flash')


async def main():
	agent = Agent(
		llm=llm,
		task='open google.com and search for the capital of France',
	)

	result = await agent.run()

	print(result)


asyncio.run(main())

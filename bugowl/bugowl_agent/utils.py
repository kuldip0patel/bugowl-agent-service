from browser_use.llm import ChatAnthropic, ChatGoogle, ChatGroq, ChatOpenAI

google_models = [
	'gemini-2.0-flash',
	'gemini-2.0-flash-exp',
	'gemini-2.0-flash-lite-preview-02-05',
	'Gemini-2.0-exp',
	'gemini-2.5-flash',
]

openai_models = [
	'gpt-4.1',
	'gpt-4.1-mini',
	'gpt-4.1-nano',
	'gpt-4.1-2025-04-14',
	'gpt-4.1-mini-2025-04-14',
	'gpt-4.1-nano-2025-04-14',
	'o4-mini',
	'o4-mini-2025-04-16',
	'o3',
	'o3-2025-04-16',
	'o3-mini',
	'o3-mini-2025-01-31',
	'o1',
	'o1-2024-12-17',
	'o1-preview',
	'o1-preview-2024-09-12',
	'o1-mini',
	'o1-mini-2024-09-12',
	'gpt-4o',
	'gpt-4o-2024-11-20',
	'gpt-4o-2024-08-06',
	'gpt-4o-2024-05-13',
	'gpt-4o-audio-preview',
	'gpt-4o-audio-preview-2024-10-01',
	'gpt-4o-audio-preview-2024-12-17',
	'gpt-4o-audio-preview-2025-06-03',
	'gpt-4o-mini-audio-preview',
	'gpt-4o-mini-audio-preview-2024-12-17',
	'gpt-4o-search-preview',
	'gpt-4o-mini-search-preview',
	'gpt-4o-search-preview-2025-03-11',
	'gpt-4o-mini-search-preview-2025-03-11',
	'chatgpt-4o-latest',
	'codex-mini-latest',
	'gpt-4o-mini',
	'gpt-4o-mini-2024-07-18',
	'gpt-4-turbo',
	'gpt-4-turbo-2024-04-09',
	'gpt-4-0125-preview',
	'gpt-4-turbo-preview',
	'gpt-4-1106-preview',
	'gpt-4-vision-preview',
	'gpt-4',
	'gpt-4-0314',
	'gpt-4-0613',
	'gpt-4-32k',
	'gpt-4-32k-0314',
	'gpt-4-32k-0613',
	'gpt-3.5-turbo',
	'gpt-3.5-turbo-16k',
	'gpt-3.5-turbo-0301',
	'gpt-3.5-turbo-0613',
	'gpt-3.5-turbo-1106',
	'gpt-3.5-turbo-0125',
	'gpt-3.5-turbo-16k-0613',
]

groq_models = ['meta-llama/llama-4-maverick-17b-128e-instruct', 'meta-llama/llama-4-scout-17b-16e-instruct', 'qwen/qwen3-32b']

anthropic_models = [
	'claude-3-7-sonnet-latest',
	'claude-3-7-sonnet-20250219',
	'claude-3-5-haiku-latest',
	'claude-3-5-haiku-20241022',
	'claude-sonnet-4-20250514',
	'claude-sonnet-4-0',
	'claude-4-sonnet-20250514',
	'claude-3-5-sonnet-latest',
	'claude-3-5-sonnet-20241022',
	'claude-3-5-sonnet-20240620',
	'claude-opus-4-0',
	'claude-opus-4-20250514',
	'claude-4-opus-20250514',
	'claude-3-opus-latest',
	'claude-3-opus-20240229',
	'claude-3-sonnet-20240229',
	'claude-3-haiku-20240307',
	'claude-2.1',
	'claude-2.0',
]


def get_llm_model(model_name: str):
	"""
	Returns the appropriate LLM model based on the provided model name.

	Args:
	    model_name (str): The name of the LLM model.

	Returns:
	    ChatOpenAI | ChatGoogle | ChatGroq | ChatAnthropic: The corresponding LLM model instance.
	"""
	if model_name in google_models:
		return ChatGoogle(model=model_name)
	elif model_name in openai_models:
		return ChatOpenAI(model=model_name)
	elif model_name in groq_models:
		return ChatGroq(model=model_name)
	elif model_name in anthropic_models:
		return ChatAnthropic(model=model_name)
	else:
		raise ValueError(f'Unsupported LLM model: {model_name}.')

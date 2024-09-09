import env
from openai import OpenAI
import time

gpt = OpenAI(api_key=env.OPENAI_KEY)

def wait_on_run(run, thread_id):
    while run.status == "queued" or run.status == "in_progress":
        run = gpt.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

def gpt_ask(question, thread_id):
    gpt_message = gpt.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question
    )

    run = gpt.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=env.ASSISTANT_ID,
    )

    run = wait_on_run(run, thread_id)

    messages = gpt.beta.threads.messages.list(
        thread_id=thread_id, order="asc", after=gpt_message.id
    )

    msg = messages.data[0].content[0].text.value

    return msg
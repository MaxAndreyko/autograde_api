from bert_rate import ContentScoreRegressor, dict_to_df
import yaml

data = {
    "Question": """
        You have received an email message from your English-speaking pen-friend Mark:

    From: Mark@mail.uk

    To: Russian_friend@ege.ru

    Subject: Household chores

    …Can you imagine we’ve just come home from the supermarket and it turned out that we spent 5 hours there! I can’t believe it! We wasted so much time shopping for food. I just hate it when mum asks me to help her with that. What about you? How do you help your parents during the week? What is your least favourite household chore? Why don’t you like doing it?

    By the way, father bought a new lawnmower last week…

    Write an email to Mark.

    In your message:

    – answer his questions;

    – ask 3 questions about his father’s lawn mower.
""",
    "Text": """
        Dear Mark, 
    Thanks for your recent e-mail. I'm always glad to get massages from you
    In your e-mail iyou asked me about household chores. Well, you know, I love helping with
    household duties, because it calms and relaxes me. During the week I wash the dishes, feed cats, water
    plants and make breakfast Mowever, I don't like to wash and sweep the floor, because I have a large house and have to spend a lot of time.
    By the way, tell me more about a father's lawn mower? Where did your father buy a lawn mower? How much did the lawn mower cost? What colour if it?
    That's all for now It's high time I helped my mom about the house. Drop me a line.
    Best wishes,
    Alyona
    """
          }

with open("config.yaml") as cfg:
    cfg_dict = yaml.safe_load(cfg)
    

df = dict_to_df(data)

model = ContentScoreRegressor(**cfg_dict["bert_model"])
print(f"Model prediction: {model.predict(df)}")
import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
import requests
import helper

load_dotenv()
TOKEN = os.getenv('TOKEN')
URL = os.getenv('URL')
URL_POINTS = os.getenv('URL_POINTS')
bot = commands.Bot(command_prefix='!')
bot.remove_command('help')
question_responses = []


@bot.event
async def on_command_error(ctx, error):
    """
    If the error is a command not found, send a message saying the command was not found.
    If the error is a check failure, send a message saying the user does not have the correct role.

    :param ctx: Context
    :param error: The error that was raised
    """
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Type !help for a list of commands.")
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')


@bot.command(name='quizz', help='Start a quiz')
async def quizz(ctx):
    """
    It gets a random question from a database,
    and adds it to a list with the one who aked for the question.

    :param ctx: the context of the command
    """

    if ctx.channel.name == 'quizz':

        # get a random question from the database
        response = requests.get(URL)
        data = response.json()
        question = random.choice(list(data.keys()))
        possibilities = list(data[question])
        possibilities.remove("points")

        # add the question to the list of questions and the user who asked it
        question_responses.append(({question: data[question]}, ctx.author))
        await ctx.send(question)

        # send the possibilities to the user
        if len(possibilities) > 1:
            text = [f"{i+1} - {value}" for i, value in enumerate(possibilities)]
            await ctx.send("\n".join(text))


@bot.command(name='points', help='Get your number of points')
async def get_points(ctx):
    """
    It gets a random question from a database,
    and adds it to a list with the one who aked for the question.

    :param ctx: the context of the command
    """

    response = requests.get(URL_POINTS)
    data = response.json()
    points = data.get(str(ctx.author.name + ctx.author.discriminator), 0)
    await ctx.send(f"Tu as {round(points, 1)} points")


@bot.command(name='stop', help='Answer a question')
async def stop(ctx):
    """
    Stop the quiz, display the correct answer, and remove the question from the list.

    :param ctx: The context of the command
    """
    if ctx.channel.name == 'quizz':
        has_user_asked, question = helper.has_user_asked(question_responses, ctx.author)
        if has_user_asked:
            possibilities = dict(list(question[0].values())[0].items())
            correct_answer = [key for key, value in possibilities.items() if value][0]
            question_responses.remove(question)
            await ctx.send(f"Quizz stopped, the answer was: {correct_answer}")


@bot.event
async def on_message(message):
    """
    Detect when the user answers a question.
    """

    if message.author == bot.user:
        return

    has_user_asked, question = helper.has_user_asked(question_responses, message.author)
    # chekc if the message has been send in the quizz channel
    if message.channel.name == 'quizz' and message.content != "!stop" and has_user_asked:

        username = str(message.author).replace("#", "")

        # question is like :
        # (
        #     {
        #         "answer1": true or false,
        #         "answer2": true or false,
        #          etc...
        #     },
        #     <discord.User object at 0x7f8b8f8b8b50>
        # )

        if message.author == question[1]:

            possibilities = dict(list(question[0].values())[0].items())
            points = possibilities.pop("points")

            if len(possibilities) > 1:
                if message.content.isdigit():
                    answer = list(possibilities.keys())[int(message.content) - 1]
                else:
                    answer = message.content
            else:
                answer = message.content

            correct_answer = [key for key, value in possibilities.items() if value][0]

            current_points = requests.get(URL_POINTS).json().get(username, 0)

            if answer == correct_answer:
                await message.channel.send('Correct!')
                question_responses.remove(question)
                new_points = current_points + points
            else:
                await message.channel.send('Incorrect!')

                # if it's a number, then play the game "less or more"
                if correct_answer.isdigit():
                    msg = "C'est moins !" if int(correct_answer) < int(
                        answer) else "C'est plus !"
                    await message.channel.send(msg)
                    points = 0.2

                new_points = current_points - points

            await message.channel.send(helper.display_points(current_points, new_points))
            requests.patch(URL_POINTS, json={username: new_points})
            # requests.patch(URL_POINTS, json={"bob": new_points})

    await bot.process_commands(message)


@bot.command(name='help', help='Get the list of commands')
async def help(ctx):
    # make an embed with the list of commands
    embed = discord.Embed(title="List of commands", description="", color=0x00ff00)
    embed.add_field(name="!quizz", value="Start a quiz", inline=False)
    embed.add_field(name="!points", value="Get your number of points", inline=False)
    embed.add_field(name="!stop", value="Stop the quizz, and get the answer", inline=False)
    embed.add_field(name="!help", value="Get the list of commands", inline=False)
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    """
    It prints the bot's name
    """
    print(f'Bot {bot.user} has connected to Discord!')

bot.run(TOKEN)

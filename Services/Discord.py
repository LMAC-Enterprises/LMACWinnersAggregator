import time
from typing import Any, Optional, List

import discord as discord
import requests
from discord import Intents, Message, File
from discord.ext import tasks


class DiscordMessage:
    _message: str
    _channelId: int
    _textFileAttachmentContent: str
    _textFileAttachmentFilename: str

    def __init__(self, message: str, channelId: int, textFileAttachmentContent: str = None,
                 textFileAttachmentFilename: str = "text.txt"):
        self._message = message
        self._channelId = channelId
        self._textFileAttachmentContent = textFileAttachmentContent
        self._textFileAttachmentFilename = textFileAttachmentFilename

    @property
    def message(self):
        return self._message

    @property
    def channelId(self):
        return self._channelId

    @property
    def textFileAttachmentContent(self):
        return self._textFileAttachmentContent

    @property
    def textFileAttachmentFilename(self):
        return self._textFileAttachmentFilename

    def __str__(self):
        return 'Discord message: {message}'.format(message=self._message)

    def __repr__(self):
        return self.__str__()


class DiscordTransponder(discord.Client):
    _channelId: int
    _messages: list
    _botName: str
    _onLastBotPostAvailableHandler: callable
    _simulate: bool

    def __init__(self, *, intents: Intents, **options: Any):
        super().__init__(intents=intents, **options)
        self._messages = []
        self._channelId = options['lookupChannelId']
        self._onLastBotPostAvailableHandler = options['onLastBotPostAvailable']
        self._botName = options['botName']
        self._simulate = options['simulate']

    async def on_ready(self):
        await self._loadLastBotPost()
        await self._sendMessages()

    async def _sendMessages(self):
        for nextMessage in self._messages:

            if self._simulate:
                print(nextMessage.message)
            else:
                channel = self.get_channel(nextMessage.channelId)
                if nextMessage.textFileAttachmentContent is None:
                    await channel.send(content=nextMessage.message)
                else:
                    with open(nextMessage.textFileAttachmentFilename, 'w') as text_file:
                        text_file.write(nextMessage.textFileAttachmentContent)

                    with open(nextMessage.textFileAttachmentFilename, 'r') as text_file:
                        await channel.send(content=nextMessage.message, file=File(
                            fp=text_file,
                            filename=nextMessage.textFileAttachmentFilename))

        self._messages = []

    def enqueueMessages(self, discordMessages: list):
        self._messages.extend(discordMessages)

    async def _loadLastBotPost(self):
        channel = self.get_channel(self._channelId)
        async for message in channel.history(limit=20):
            if self._botName == message.author.name and len(message.attachments) >= 1:
                file = requests.get(message.attachments[0].url)
                self._onLastBotPostAvailableHandler(file.content.decode())

    def waitUntilMessageAreSent(self):
        timeout = 10
        while len(self._messages) > 0:
            if timeout <= 0:
                return
            time.sleep(1.00)
            timeout -= 1


    @staticmethod
    def create(lookupChannelId: int, discordBotName: str, onLastBotPostAvailableHandler: callable, simulate: bool) -> "DiscordTransponder":
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        return DiscordTransponder(
            intents=intents,
            lookupChannelId=lookupChannelId,
            botName=discordBotName,
            onLastBotPostAvailable=onLastBotPostAvailableHandler,
            simulate=simulate
        )


# class DiscordDispatcher:
#     _instance = None
#     _messageQueue: list
#     _channelId: int
#     _simulate: bool
#     _transponder: Optional[DiscordTransponder]
#
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(DiscordDispatcher, cls).__new__(cls)
#             cls._messageQueue = []
#             cls._simulate = False
#             cls._channelId = 0
#             cls._transponder = None
#
#         return cls._instance
#
#     def enqueueMessage(self, message: str, textFileAttachmentContent: str = None, textFileAttachmentFilename: str = ''):
#         self._messageQueue.append(DiscordMessage(message, self._channelId, textFileAttachmentContent, textFileAttachmentFilename))
#
#     def enterChatroom(self, channelId: int):
#         self._channelId = channelId
#
#     async def loopTask(self):
#         await self._transponder.wait_until_ready()
#         while True:
#             await asyncio.sleep(1)
#             print('Running')
#
#     def startClient(self, discordToken: str, lookupChannelId: int):
#         intents = discord.Intents.default()
#         intents.messages = True
#
#         self._transponder = DiscordTransponder(messages=self._messageQueue, intents=intents, lookupChannelId=lookupChannelId)
#
#         loop = asyncio.get_event_loop()
#         loop.create_task(self._transponder.start(discordToken))
#
#
#
#
#     def runTasks(self):
#         if self._simulate:
#             print('Running discord tasks: {tasks}'.format(tasks=str(self._messageQueue)))
#             return
#
#         if len(self._messageQueue) == 0:
#             return
#
#         self._transponder.enqueueMessages(self._messageQueue)
#
#     def setSimulationMode(self, simulate: bool):
#         self._simulate = simulate
#
#     def waitUntilReady(self):
#         while not self._transponder.isClientReady:
#             time.sleep(0.5)
#
#     def getLastNominationFile(self, username: str, channelId: int) -> str:
#         messages = self._transponder.getLookupHistory()
#
#         for message in messages:
#             if username != message.author.name:
#                 continue
#
#             if len(message.attachments) < 1:
#                 continue
#
#             file = requests.get(message.attachments[0].url)
#             return file.content.decode()
#
#         return None
#
#     def close(self):
#         self._transponder.close()

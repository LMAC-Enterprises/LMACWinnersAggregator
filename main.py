import argparse
import asyncio
import json
import logging
import signal
import time
from asyncio import AbstractEventLoop
from typing import Optional

from Services.Discord import DiscordTransponder, DiscordMessage
from Services.HiveAspect import LatestWinnersLoader
from Services.Nominations import NominationFile


class Main:
    EXITCODE_OK = 0
    EXITCODE_ERROR = 1

    _args: argparse.Namespace
    _config: dict
    _discordTransponder: Optional[DiscordTransponder]
    _loop: AbstractEventLoop

    def __init__(self, TESTING=None):
        self._discordTransponder = None

        logging.basicConfig(
            format="%(asctime)s|%(levelname)s|%(message)s",
            level=logging.INFO if TESTING else logging.WARNING,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        self._config = {
            'discord_token': ''
        }

        with open('config.json') as cf:
            self._config = json.load(cf)

        parser = argparse.ArgumentParser()
        parser.description = 'Aggregates the winners of an LMAC round and writes in into a special data sheet.'
        parser.add_argument('-s', '--simulate', default=False, help='No action to will pe performed.')

        self._args = parser.parse_args()

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self._discordTransponder = DiscordTransponder.create(
            self._config['discord_lookup_channel_id'],
            self._config['discord_bot_name'],
            self.onLastBotPostAvailable,
            self._args.simulate
        )

        self._mainLoop()

    # def _initialize(self):
    #     discordDispatcher = DiscordDispatcher()
    #     discordDispatcher.setSimulationMode(self._args.simulate)
    #     discordDispatcher.startClient(self._config['discord_token'], self._config['discord_lookup_channel_id'])
    #     # discordDispatcher.waitUntilReady()
    #
    #     return True
    #
    # def _perform(self):
    #     discordDispatcher = DiscordDispatcher()
    #     print(0)
    #     text = discordDispatcher.getLastNominationFile(
    #         self._config['discord_bot_name'],
    #         self._config['discord_lookup_channel_id'],
    #     )
    #     print()
    #     if text is None:
    #         return False
    #     print(1)
    #     latestWinnerLoader = LatestWinnersLoader('lmac', NominationFile.nominees(text))
    #     winners = latestWinnerLoader.getWinners()
    #     if len(winners.keys()) == 0:
    #         return False
    #     print(2)
    #     text = NominationFile.sortByWeighting(text, winners)
    #     if not text:
    #         return False
    #     print(3)
    #     discordDispatcher.enqueueMessage('Winners.', text, 'winners.txt')
    #
    #     return True
    #
    # def _finish(self):
    #     discordDispatcher = DiscordDispatcher()
    #     discordDispatcher.runTasks()
    #     ## discordDispatcher.close()
    #
    #     return True

    def _sendDiscordMessage(self, message: str, channelId: int, textFileAttachmentContent: str = None,
                            textFileAttachmentFilename: str = ''):
        self._discordTransponder.enqueueMessages(
            [DiscordMessage(
                message,
                channelId,
                textFileAttachmentContent,
                textFileAttachmentFilename
            )]
        )

    def onLastBotPostAvailable(self, nominees: str):

        if not nominees:
            self._sendDiscordMessage(
                'Error: Can\'t find the file containing the nominees. Please check the Nomination Aggregator Bot.',
                self._config['discord_lookup_channel_id']
            )
        else:
            latestWinnerLoader = LatestWinnersLoader('lmac', NominationFile.nominees(nominees))
            winners = latestWinnerLoader.getWinners()
            if len(winners.keys()) == 0:
                self._sendDiscordMessage(
                    'Error: The file containing the nominees is corrupted. Please check the Nomination Aggregator Bot.',
                    self._config['discord_lookup_channel_id']
                )
            else:
                text = NominationFile.sortByWeighting(nominees, winners)
                if not text:
                    self._sendDiscordMessage(
                        'Error: The file containing the nominees is corrupted. Please check the Nomination Aggregator Bot.',
                        self._config['discord_lookup_channel_id']
                    )
                else:
                    self._sendDiscordMessage(
                        'Winners.',
                        self._config['discord_lookup_channel_id'],
                        text,
                        'winners.txt'
                    )

        self._discordTransponder.waitUntilMessageAreSent()


    def _mainLoop(self):
        self._loop.create_task(
            self._discordTransponder.start(
                self._config['discord_token']
            )
        )

        try:
            for s in signal.SIGINT, signal.SIGTERM:
                self._loop.add_signal_handler(s, lambda: self._loop.create_task(self._discordTransponder.close()))
        except NotImplementedError:
            pass

        try:
            self._loop.run_forever()
        except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
            self._loop.run_until_complete(self._discordTransponder.close())
        except Exception:
            logging.critical("Bot has crashed", exc_info=True)
            self._loop.run_until_complete(self._discordTransponder.close())
        finally:
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            asyncio.set_event_loop(None)
            self._loop.stop()
            self._loop.close()


if __name__ == '__main__':
    Main()

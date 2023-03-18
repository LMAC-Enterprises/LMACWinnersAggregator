from beem import Hive
from beem.comment import AccountPosts


class LatestWinnersLoader:
    _winners: dict

    def __init__(self, lookupUsername: str, pollOptions: list):
        hive = Hive()
        comments = AccountPosts(account='lmac', limit=5, sort='posts', blockchain_instance=hive)
        self._winners = {}

        for comment in comments:
            if 'final-poll' not in comment.permlink:
                continue
            for replyComment in comment.get_replies():
                if not replyComment.body.startswith('@'):
                    continue
                replyBody = replyComment.body.strip()
                if replyBody in pollOptions:
                    self._winners[replyBody] = replyComment.reward.amount
            break

    def getWinners(self) -> dict:
        return self._winners

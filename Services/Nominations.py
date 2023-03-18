import re


class NominationFile:
    @staticmethod
    def nominees(nominationFileText: str) -> list:
        nomineeList = []
        matches = re.finditer(r"(@[a-zA-Z0-9_\.\-]+)\n", nominationFileText, re.MULTILINE)
        for i, match in enumerate(matches, start=1):
            nomineeList .append(match.group(1))

        return nomineeList

    @staticmethod
    def sortByWeighting(nominationFileText: str, winnerWeights: dict) -> str:
        nomineeList = []
        matches = re.finditer(r"(@[a-zA-Z0-9_\.\-]+)\n(.*)\n(.*)\n\n", nominationFileText, re.MULTILINE)
        for i, match in enumerate(matches, start=1):
            nomineeList.append({
                'author': str(match.group(1)),
                'post': str(match.group(2)),
                'image': str(match.group(3)),
                'weight': winnerWeights[str(match.group(1))]
            })

        nomineeList.sort(key=lambda k: k['weight'], reverse=True)

        newNomineeFileText = ''

        for nominee in nomineeList:
            newNomineeFileText += nominee['author'] + "\n"
            newNomineeFileText += nominee['post'] + "\n"
            newNomineeFileText += nominee['image'] + "\n"
            newNomineeFileText += "\n"

        return newNomineeFileText

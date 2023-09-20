# 1) In your application, redirect the user to shikimori authorization page
# https://shikimori.me/oauth/authorize?client_id=bce7ad35b631293ff006be882496b29171792c8839b5094115268da7a97ca34c&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&response_type=code&scope=user_rates+messages+comments+topics+content+clubs+friends+ignores
# There the user must authorize your application so you could receive an authorization token.
#
import requests
import time

debug = True


def debugger(message):
    if debug:
        print(message)


# object loads anime lists for specific user of shikimory

class shikiAPI:
    UserAgent = "Api Test"
    headers = {"User-Agent": UserAgent}
    shikiEndpoint = 'https://shikimori.me'


class animeListAccembler(shikiAPI):
    userId = -1
    animeList = []
    animeStatuses = ['planned', 'watching', 'rewatching', 'completed', 'on_hold', 'dropped']

    def loadAnimeList(self, userData: str):
        if userData.isdigit():
            self.checkUserId(userData)
            self.loadAnimeListByUserId(userData)
        else:
            self.loadAnimeListByUserNickname(userData)

    def checkUserId(self, userId):
        res = requests.get(self.shikiEndpoint + f'/api/users/{userId}',
                           headers=self.headers)
        if res.status_code == 200:
            resJSON = res.json()
            self.userId = resJSON['id']
            return True
        else:
            return False

    def loadAnimeListByUserId(self, userId):
        for status in ['watching', 'rewatching', 'completed']:
            if not self.loadAnimeListByUserIdAndStatus(userId, status):
                return False
        return True

    def loadAnimeListByUserIdAndStatus(self, userId, status):
        if not (status in self.animeStatuses):
            debugger(f'status {status} is not exist')
            return False

        data = {
            "limit": 5000,
            "status": status
        }
        res = requests.get(self.shikiEndpoint + f'/api/users/{userId}/anime_rates',
                           headers=self.headers, data=data)
        if res.status_code != 200:
            debugger("error in getAnimeListByUserId " + res.text)
            return False

        statusList = []
        resJSON = res.json()
        for item in resJSON:
            statusList.append(
                item['anime']['id']
                #{item['anime']['id']: item['anime']['name']}
            )

        self.animeList.append([status, statusList])
        return True

    def loadAnimeListByUserNickname(self, nickname):
        if not self.loadUserIdByNickname(nickname):
            debugger(f'user {nickname} not found')
            return False

        return self.loadAnimeListByUserId(self.userId)

    def loadUserIdByNickname(self, nickname):
        res = requests.get(self.shikiEndpoint + f'/api/users/{nickname}',
                           headers=self.headers, data={"is_nickname": 1})
        if res.status_code == 200:
            resJSON = res.json()
            self.userId = resJSON['id']
            return True
        else:
            return False

    def getStatusedAnime(self, status):
        if not (status in self.animeStatuses):
            debugger(f'status {status} is not exist')
            return False

        # [statusName, list]
        for statusedList in self.animeList:
            if statusedList[0] == status:
                return statusedList[1]

        return None

    def getAnimeList(self):
        return self.animeList


class franchiseChecker(shikiAPI):
    watched = []
    plainList = []
    checked = []
    unwatched = []

    def __init__(self, animeListObject: animeListAccembler):
        self.watched = animeListObject.getStatusedAnime('completed')
        self.makePlainList(animeListObject)
        self.checkAnimes()

    def makePlainList(self, animeListObject: animeListAccembler):
        animeStatucedList = animeListObject.getAnimeList()
        plainList = []
        for animeList in animeStatucedList:
            if animeList[0] == 'completed': continue
            plainList += animeList[1]
        self.plainList = plainList

    def checkAnimes(self):
        for animeId in self.watched:
            self.checkFranchise(animeId)

    def checkFranchise(self, animeId: int):
        if animeId in self.checked:  # if we watched franchise, we don't want to check one franchise many times
            return None

        animeInFranchise = self.loadFranchise(animeId)
        if animeInFranchise == []:
            return False
        for anime in animeInFranchise:
            self.checked.append(anime['id'])
            if (anime['id'] in self.watched) or (anime['id'] in self.plainList): continue
            self.unwatched.append(anime)
        return True

    def loadFranchise(self, animeId: int):
        res = requests.get(self.shikiEndpoint + f'/api/animes/{animeId}/franchise', headers=self.headers)

        if res.status_code == 429:
            time.sleep(1)
            return self.loadFranchise(animeId)
        elif res.status_code != 200:
            debugger(f'loadFranchise error: {res.text} {res.status_code} : {animeId}')
            return []

        resJSON = res.json()

        return resJSON['nodes']

    def getUnwatched(self):
        return self.unwatched

# TODO:
# check if released
# make setting to check if summary/TV serial/etc..

if __name__ == '__main__':
    list = animeListAccembler()
    list.loadAnimeList('MajorOvosch')
    print(list.getAnimeList())

    checker = franchiseChecker(list)
    print(checker.getUnwatched())
    print(checker.checked)
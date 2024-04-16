from os import listdir
from os.path import isfile, join

class BreakLoop(Exception):
    pass

def getAllFiles(directoryPath):
    return [f for f in listdir(directoryPath) if isfile(join(directoryPath, f))]


def readFile(filename):
    file = open(filename, 'r', encoding='utf-16')
    headers = file.readline().strip().split('\t')

    result = []
    for line in file:
        data = line.strip().split('\t')
        row = dict()

        for i in range(len(headers)):
            row[headers[i]] = data[i]

        result.append(row)

    file.close()

    return result


def getValidLeagues(leagues):
    leaguesIds = set()
    validLeaguesIndexes = set()
    for index, oneLeague in enumerate(leagues):
        if (
                oneLeague["iswomencompetition"] == '0' and
                len(oneLeague["leaguename"]) != 0 and
                oneLeague["leaguename"].lower() != "international" and
                oneLeague["countryid"] != '0' and
                oneLeague["leagueid"] not in {'383', '382', '384'}
        ):
            leaguesIds.add(oneLeague['leagueid'])
            validLeaguesIndexes.add(index)

    return leaguesIds, validLeaguesIndexes


def teamsToDictionary(teams):
    result = dict()
    for oneTeam in teams:
        if len(oneTeam['teamname']) != 0:
            result[oneTeam["teamid"]] = oneTeam

    return result


def removeRedundantLeagueTeamsLinks(leagueteamlinks, leaguesIds):
    result = dict()
    for oneId in leaguesIds:
        result[oneId] = dict()

    #Can here be a problem with Arsenal cause empty teams have the id 1 as well?
    for oneLink in leagueteamlinks:
        if oneLink["leagueid"] in leaguesIds:
            result[oneLink["leagueid"]][oneLink["teamid"]] = oneLink

    return result


def removeRedundantTeams(teams, leagueteamslink):
    validTeams = set()
    for oneLeague in leagueteamslink:
        validTeams.update(set(leagueteamslink[oneLeague].keys()))

    result = dict()
    for oneTeam in teams:
        if oneTeam["teamid"] in validTeams and len(oneTeam["teamname"]) != 0:
            result[oneTeam["teamid"]] = oneTeam

    return result


def removeRedundantCompetitions(competitions, leaguesId):
    result = dict()

    for oneCompetition in competitions:
        if oneCompetition["competitionid"] in leaguesId:
            result[oneCompetition["competitionid"]] = oneCompetition

    return result


def formRatingByCountry(leagues, leagueteamslink, teams):
    countries = dict()
    countriesLeagues = dict()

    for oneLeague in leagueteamslink:
        countryId = leagues[oneLeague]["countryid"]
        if countryId not in countriesLeagues:
            countriesLeagues[countryId] = dict()
        countriesLeagues[countryId][oneLeague] = len(leagueteamslink[oneLeague])

        if leagues[oneLeague]["level"] != '1':
            continue
        sum = 0
        for oneTeam in leagueteamslink[oneLeague]:
            sum += int(teams[oneTeam]['overallrating'])

        countries[countryId] = sum / len(leagueteamslink[oneLeague])

    result = dict(sorted(countries.items(), key=lambda item: item[1], reverse=True))
    for oneCountry in result:
        amount = 0
        for oneLeague in countriesLeagues[oneCountry]:
            amount += countriesLeagues[oneCountry][oneLeague]

        result[oneCountry] = dict({amount: list(countriesLeagues[oneCountry].keys())})

    return result


def formRegionData(countriesGroup, leagues, leagueteamlink, teams):
    leaguesRegion = dict()
    teamsRegion = dict()

    for oneRegion in countriesGroup:
        leaguesRegion[oneRegion] = []
        teamsRegion[oneRegion] = []

    for oneLeague in leagues:
        for oneRegion in countriesGroup:
            if leagues[oneLeague]["countryid"] in countriesGroup[oneRegion]:
                leaguesRegion[oneRegion].append(oneLeague)
                teamsRegion[oneRegion].extend(list(leagueteamlink[oneLeague].keys()))

    for oneRegion in teamsRegion:
        teamsDictionary = dict()
        for oneTeam in teamsRegion[oneRegion]:
            teamsDictionary[oneTeam] = teams[oneTeam]

        teamsDictionary = dict(sorted(teamsDictionary.items(), key=lambda item: item[1]["overallrating"], reverse=True))
        teamsRegion[oneRegion] = teamsDictionary

    return leaguesRegion, teamsRegion


def formRatingByRegion(countriesGroup, countriesByRating, leagues):
    result = dict()
    for oneRegion in countriesGroup:
        result[oneRegion] = []

    for oneCountry in countriesByRating:
        for oneRegion in countriesGroup:
            if oneCountry not in countriesGroup[oneRegion]:
                continue

            for size in countriesByRating[oneCountry]:
                level = list()
                for oneLeague in countriesByRating[oneCountry][size]:
                    level.append(tuple([leagues[oneLeague]["level"], oneLeague]))

                level = sorted(level, key=lambda item: item[0])
                result[oneRegion].extend([dict({list(countriesByRating[oneCountry].keys())[0]: [value[1] for value in level]})])
    return result


def formLeagueTeamLinks(regionRating, teamsByRegion, leagueteamlinks):
    newLeagueteamlinks = dict()
    for oneRegion in teamsByRegion:
        teamsByRegion[oneRegion] = list(teamsByRegion[oneRegion].values())

    try:
        for oneRegion in list(teamsByRegion.keys()):
            queue = list(teamsByRegion.keys())
            for leaguesData in regionRating[oneRegion]:
                countryCapacity = list(leaguesData.keys())[0]
                counter = 0
                while len(teamsByRegion[queue[0]]) < countryCapacity:
                    if counter == len(queue):
                        raise BreakLoop
                    counter += 1
                    queue.append(queue.pop(0))

                for oneLeague in leaguesData[countryCapacity]:
                    newLeagueteamlinks[oneLeague] = teamsByRegion[queue[0]][:len(leagueteamlinks[oneLeague])]
                    teamsByRegion[queue[0]] = teamsByRegion[queue[0]][len(leagueteamlinks[oneLeague]):]
                queue.append(queue.pop(0))
    except BreakLoop:
        pass

    return newLeagueteamlinks

    print(newLeagueteamlinks)
# def parseLeaguesTeams(leagues, leagueteamslink, teams):
#     leaguesSize = dict()
#     teams = dict()
#
#     for oneTeam in teams:
#         if oneTeam[]

countriesGroups = dict({
    'Europe': ['14', '45', '27', '21', '18', '38', '48', '7', '34', '13', '47', '42', '10', '4', '12', '37', '51', '39', '46', '36', '22', '25'],
    'America': ['54', '52', '225', '95'],
    'Asia': ['183', '167', '195', '155', '159']
})
files = getAllFiles('./files')
result = dict()
for oneFile in files:
    name = oneFile.split('.txt')[0]
    result[name] = readFile('./files/' + oneFile)

validLeagues, validLeaguesIndexes = getValidLeagues(result["leagues"])
result["leagues"] = {value["leagueid"]: value for key, value in enumerate(result["leagues"]) if key in validLeaguesIndexes}
result["leagueteamlinks"] = removeRedundantLeagueTeamsLinks(result["leagueteamlinks"], result["leagues"].keys())
result["teams"] = removeRedundantTeams(result["teams"], result["leagueteamlinks"])
result["competition"] = removeRedundantCompetitions(result["competition"], result["leagues"].keys())
countryRating = formRatingByCountry(result["leagues"], result["leagueteamlinks"], result["teams"])
regionRating = formRatingByRegion(countriesGroups, countryRating, result["leagues"])
leaguesByRegion, teamsByRegion = formRegionData(countriesGroups, result["leagues"], result["leagueteamlinks"], result["teams"])
newLeaguesTeamLinks = formLeagueTeamLinks(regionRating, teamsByRegion, result["leagueteamlinks"])
import re
import requests
import datetime
from bs4 import BeautifulSoup
from datetime import date
import pandas as pd

def get_parsed_page(url):
    # This fixes a blocked by cloudflare error i've encountered
    headers = {
        "referer": "https://www.hltv.org/stats",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    return BeautifulSoup(requests.get(url, headers=headers).text, "lxml")

def top5teams():
    home = get_parsed_page("http://hltv.org/")
    count = 0
    teams = []
    for team in home.find_all("div", {"class": ["col-box rank"], }):
        count += 1
        teamname = team.text[3:]
        teams.append(teamname)
    return teams

def top30teams():
    page = get_parsed_page("http://www.hltv.org/ranking/teams/")
    teams = page.find("div", {"class": "ranking"})
    teamlist = []
    for team in teams.find_all("div", {"class": "ranked-team standard-box"}):
        newteam = {'name': team.find('div', {"class": "ranking-header"}).select('.name')[0].text.strip(),
                   'rank': converters.to_int(team.select('.position')[0].text.strip(), regexp=True),
                   'rank-points': converters.to_int(team.find('span', {'class': 'points'}).text, regexp=True),
                   'team-id': converters.to_int(team.find('a', {'class': 'details moreLink'})['href'].split('/')[-1]),
                   'team-players': []}
        for player_div in team.find_all("td", {"class": "player-holder"}):
            player = {}
            player['name'] = player_div.find('img', {'class': 'playerPicture'})['title']
            player['player-id'] = converters.to_int(player_div.select('.pointer')[0]['href'].split("/")[-2])
            newteam['team-players'].append(player)
        teamlist.append(newteam)
    return teamlist



def get_old_matches(url):
    page = get_parsed_page(url)
    all_matches = page.find_all("div", {"class": "result-con"})
    matches_url = []
    for match in all_matches:
        matches_url.append('https://www.hltv.org' + match.find('a', {'class': 'a-reset'})['href'])
    return matches_url


def top_players():
    page = get_parsed_page("https://www.hltv.org/stats")
    players = page.find_all("div", {"class": "col"})[0]
    playersArray = []
    for player in players.find_all("div", {"class": "top-x-box standard-box"}):
        playerObj = {}
        playerObj['country'] = player.find_all('img')[1]['alt'].encode('utf8')
        buildName = player.find('img', {'class': 'img'})['alt'].split("'")
        playerObj['name'] = buildName[0].rstrip() + buildName[2]
        playerObj['nickname'] = player.find('a', {'class': 'name'}).text.encode('utf8')
        playerObj['rating'] = player.find('div', {'class': 'rating'}).find('span', {'class': 'bold'}).text.encode('utf8')
        playerObj['maps-played'] = player.find('div', {'class': 'average gtSmartphone-only'}).find('span', {'class': 'bold'}).text.encode('utf8')

        playersArray.append(playerObj)
    return playersArray


def get_team_names(match):
    dicty = {}
    page = get_parsed_page(match)
    team_names = page.find_all("div", {"class": "teamName"})
    dicty.update({'team1':team_names[0].text,'team2':team_names[1].text,'url':match})
    return dicty

def get_players(teamid):
    page = get_parsed_page(teamid)
    titlebox = page.find("div", {"class": "bodyshot-team"})
    players = []
    try:
        for player_link in titlebox.find_all("a"):
            players.append('https://www.hltv.org/stats' + player_link['href'].replace('player','players'))
        return players
    except:
        pass

def get_teams_in_match(match):
    teams = {}
    page = get_parsed_page(match)
    output = []
    for i in range(1,3):
        team = page.find('div',{"class":"team"+str(i)+"-gradient"})
        if team != None:
            try:
                team = team.find('a')['href']
                output.append('https://www.hltv.org'+team)
            except:
                pass
    return output

def get_team_history(team):
    outcome_versus_initial_team = {}
    teams_to_be_scrapped = []
    results_dataframe = pd.DataFrame()
    page = get_parsed_page(team+'#tab-statsBox')
    last_5_mateches = page.find_all('a',{"class":"highlighted-stat text-ellipsis"})
    current_team = page.find('div',{'class','profile-team-info'})
    current_team = current_team.find('div',{'class':'profile-team-name text-ellipsis'}).text
    for match in last_5_mateches:
        team_id = match.find('img',{"class":'team-logo'})['src'][match.find('img',{"class":'team-logo'})['src'].find('logo/')+5:len(match.find('img',{"class":'team-logo'})['src'])]
        team_name = match.find('img',{"class":'team-logo'})['alt']
        outcome = match.find('div',{'class':'highlighted-match-status'}).text
        outcome_versus_initial_team.update({'out team':team_name,'in team':current_team,'Result':outcome,'team_url':'https://www.hltv.org/team/'+str(team_id)+'/'+team_name.replace(' ','-')})
        results_dataframe = results_dataframe.append(outcome_versus_initial_team,ignore_index=True)
    return results_dataframe

def get_winner(match):
    page = get_parsed_page(match)
    team = page.find("div",{"class":"teamName"}).text
    match_over = page.find("div",{"class":"countdown"})
    if 'Match over' in match_over.text:
        try:
            won = page.find_all("div",{"class":"won"})[1].text.replace('\n','')
            return 1
        except:
            return 0
    else:
        return 2

def get_player_stats(player,day,mapp):
    #?startDate=2019-11-06&endDate=2019-12-06
    data = date.today() - datetime.timedelta(days=day)
    page = get_parsed_page(player+'?startDate='+data.strftime('%Y-%m-%d')+'&endDate='+date.today().strftime('%Y-%m-%d')+'&maps='+mapp)
    stats = page.find_all("div", {"class": "col stats-rows standard-box"})
    statisc = {}
    team = page.find("a",{"class":"a-reset text-ellipsis"}).text
    player_name = page.find("h1",{"class":"summaryNickname text-ellipsis"}).text
    statisc.update({'Team':team,'Player':player_name})
    for stat in stats:
        for player_link in stat.find_all("div"):
            rows = stat.find_all("span")
            y=0
            while y < len(rows):
                #print(rows[y].text + '  -  ' + rows[y+1].text)
                statisc.update({rows[y].text:rows[y+1].text.replace('%','')})
                y= y+2
    #print(statisc)
    return statisc

def scrap_players_by_team(team):
    output = pd.DataFrame()
    players = get_players(team)
    try:
        for player in players:
            output = output.append(get_player_stats(player,30), ignore_index=True)
        return output
    except:
        pass

def get_team_power(team_):
    output = {}
    team_score = scrap_players_by_team(team_)
    try:
        team_score['Assists / round'] = team_score['Assists / round'].astype(float)
        team_score['Damage / Round'] = team_score['Damage / Round'].astype(float)
        team_score['Grenade dmg / Round'] = team_score['Grenade dmg / Round'].astype(float)
        team_score['Kills / round'] = team_score['Kills / round'].astype(float)
        team_score['Saved by teammate / round'] = team_score['Saved by teammate / round'].astype(float)
        team_score['Deaths / round'] = team_score['Deaths / round'].astype(float)
        team_score['Rounds played'] = team_score['Rounds played'].astype(float)
        team_score['Total kills'] = team_score['Total kills'].astype(float)
        team_score['Total deaths'] = team_score['Total deaths'].astype(float)
        team_score['Rating 2.0'] = team_score['Rating 2.0'].astype(float)
        team_score['K/D Ratio'] = team_score['K/D Ratio'].astype(float)
        team_score['Saved teammates / round'] = team_score['Saved teammates / round'].astype(float)
        team_score['Round Performance'] = (team_score['Assists / round'] * team_score['Damage / Round'] * team_score['Grenade dmg / Round'] * team_score['Kills / round'] * team_score['Saved by teammate / round']*team_score['Saved teammates / round']) / team_score['Deaths / round']
        team_score['Overall Performance'] = (team_score['Rounds played'] * team_score['Total kills']) / team_score['Total deaths']
        team_score['Gain'] =  team_score['Round Performance'] / team_score['Overall Performance']
        team_score = team_score[['Rating 2.0','K/D Ratio','Round Performance','Overall Performance','Gain','Team']].copy()
        missing_players = {}
        missing_players.update({'Rating 2.0':team_score['Rating 2.0'].mean(),'K/D Ratio':team_score['K/D Ratio'].mean(),'Round Performance':team_score['Round Performance'].mean(),'Overall Performance':team_score['Overall Performance'].mean(),'Gain':team_score['Gain'].mean()})
        players_add = 5 - len(team_score)
        if players_add > 0:
            for i in range(players_add):
                team_score = team_score.append(missing_players,ignore_index=True)
        
        output.update({'Team':team_score['Team'][0],'Rating 2.0':round(team_score['Rating 2.0'].sum(),2),'K/D Ratio':round(team_score['K/D Ratio'].sum(),2),'Round Performance':round(team_score['Round Performance'].sum(),2),'Overall Performance':round(team_score['Overall Performance'].sum(),2),'Gain':round(team_score['Gain'].sum(),4)})
    except:
        pass
    return output


def get_matches():
    output = pd.DataFrame()
    matches = get_parsed_page("http://www.hltv.org/matches/")
    matches_list = {}
    upcomingmatches = matches.find("div", {"class": "upcoming-matches"})

    matchdays = upcomingmatches.find_all("div", {"class": "match-day"})

    for match in matchdays:
        matchDetails = match.find_all("div", {"class": "match"})

        for getMatch in matchDetails:
            matchObj = {}

            matchObj['date'] = getMatch.find("span", {"class": "standard-headline"})
            matchObj['ulr'] = 'https://www.hltv.org' + getMatch.find("a",{"class":"a-reset"})['href'].replace('/betting/analytics','')
            matchObj['time'] = getMatch.find("td", {"class": "time"}).text.replace('\n','')
            if (getMatch.find("td", {"class": "placeholder-text-cell"})):
                matchObj['event'] = getMatch.find("td", {"class": "placeholder-text-cell"})
            elif (getMatch.find("td", {"class": "event"})):
                matchObj['event'] = getMatch.find("td", {"class": "event"}).text
            else:
                matchObj['event'] = None

            if (getMatch.find_all("td", {"class": "team-cell"})):
                matchObj['team1'] = getMatch.find_all("td", {"class": "team-cell"})[0].text.replace('\n','')
                matchObj['team2'] = getMatch.find_all("td", {"class": "team-cell"})[1].text.replace('\n','')
            else:
                matchObj['team1'] = None
                matchObj['team2'] = None
            output = output.append(matchObj, ignore_index=True)
    return output

def get_results():
    results = get_parsed_page("http://www.hltv.org/results/")

    results_list = []

    pastresults = results.find_all("div", {"class": "results-holder"})

    for result in pastresults:
        resultDiv = result.find_all("div", {"class": "result-con"})

        for res in resultDiv:
            getRes = res.find("div", {"class": "result"}).find("table")

            resultObj = {}

            if (res.parent.find("span", {"class": "standard-headline"})):
                resultObj['date'] = res.parent.find("span", {"class": "standard-headline"}).text.encode('utf8')
            else:
                dt = datetime.date.today()
                resultObj['date'] = str(dt.day) + '/' + str(dt.month) + '/' + str(dt.year)

            if (res.find("td", {"class": "placeholder-text-cell"})):
                resultObj['event'] = res.find("td", {"class": "placeholder-text-cell"}).text.encode('utf8')
            elif (res.find("td", {"class": "event"})):
                resultObj['event'] = res.find("td", {"class": "event"}).text.encode('utf8')
            else:
                resultObj['event'] = None

            if (res.find_all("td", {"class": "team-cell"})):
                resultObj['team1'] = res.find_all("td", {"class": "team-cell"})[0].text.encode('utf8').lstrip().rstrip()
                resultObj['team1score'] = converters.to_int(res.find("td", {"class": "result-score"}).find_all("span")[0].text.encode('utf8').lstrip().rstrip())
                resultObj['team2'] = res.find_all("td", {"class": "team-cell"})[1].text.encode('utf8').lstrip().rstrip()
                resultObj['team2score'] = converters.to_int(res.find("td", {"class": "result-score"}).find_all("span")[1].text.encode('utf8').lstrip().rstrip())
            else:
                resultObj['team1'] = None
                resultObj['team2'] = None

            results_list.append(resultObj)

    return results_list

def get_results_by_date(start_date, end_date):
    # Dates like yyyy-mm-dd  (iso)
    results_list = []
    offset = 0
    # Loop through all stats pages
    while True:
        url = "https://www.hltv.org/stats/matches?startDate="+start_date+"&endDate="+end_date+"&offset="+str(offset)

        results = get_parsed_page(url)

        # Total amount of results of the query
        amount = int(results.find("span", attrs={"class": "pagination-data"}).text.split("of")[1].strip())

        # All rows (<tr>s) of the match table
        pastresults = results.find("tbody").find_all("tr")

        # Parse each <tr> element to a result dictionary
        for result in pastresults:
            team_cols = result.find_all("td", {"class": "team-col"})
            t1 = team_cols[0].find("a").text
            t2 = team_cols[1].find("a").text
            t1_score = int(team_cols[0].find_all(attrs={"class": "score"})[0].text.strip()[1:-1])
            t2_score = int(team_cols[1].find_all(attrs={"class": "score"})[0].text.strip()[1:-1])
            map = result.find(attrs={"class": "statsDetail"}).find(attrs={"class": "dynamic-map-name-full"}).text
            event = result.find(attrs={"class": "event-col"}).text
            date = result.find(attrs={"class": "date-col"}).find("a").find("div").text

            result_dict = {"team1": t1, "team2": t2, "team1score": t1_score,
                           "team2score": t2_score, "date": date, "map": map, "event": event}

            # Add this pages results to the result list
            results_list.append(result_dict)

        # Get the next 50 results (next page) or break
        if offset < amount:
            offset += 50
        else:
            break

    return results_list

if __name__ == "__main__":
    import pprint
    pp = pprint.PrettyPrinter()
    
    pp.pprint('top5')
    pp.pprint(top5teams())

    pp.pprint('top30')
    pp.pprint(top30teams())
    
    pp.pprint('top_players')
    pp.pprint(top_players())
    
    pp.pprint('get_players')
    pp.pprint(get_players('6665'))
    
    pp.pprint('get_team_info')
    pp.pprint(get_team_info('6665'))

    pp.pprint('get_matches')
    pp.pprint(get_matches())

    pp.pprint('get_results')
    pp.pprint(get_results())

    pp.pprint('get_results_by_date')
    today_iso = datetime.datetime.today().isoformat().split('T')[0]
    pp.pprint(get_results_by_date(today_iso, today_iso))
   
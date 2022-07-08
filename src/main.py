import datetime
import json
import googleapiclient.discovery
import googleapiclient.errors
import isodate
from itertools import islice, takewhile, repeat, chain
import bs4
import requests


scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
api_service_name = "youtube"
api_version = "v3"
with open("CLIENT_SECRET.json", "r") as f:
    api_key = json.load(f)["APIKEY"]

youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)


def split_every(n, iterable):
    iterator = iter(iterable)
    return takewhile(bool, (list(islice(iterator, n)) for _ in repeat(None)))


def get_channel_id_from_youtube_url(url):
    soup = bs4.BeautifulSoup(requests.get(url).text, "html.parser", parse_only=bs4.SoupStrainer("meta"))
    return soup.find("meta", attrs={"itemprop": "channelId"}).get("content")


def get_video_ids_from_channel_id(channel_id):
    response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    ids = []
    page_token = ""
    while True:
        response = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=page_token
        ).execute()

        ids.extend(map(lambda x: x["contentDetails"]["videoId"], response["items"]))

        if "nextPageToken" in response:
            page_token = response["nextPageToken"]
        else:
            break
    return ids


def get_video_list_responses_from_ids(ids, part="contentDetails,statistics"):
    return list(chain.from_iterable(
        youtube.videos().list(
            part=part,
            id=",".join(chunk)
        ).execute()["items"] for chunk in split_every(50, ids)
    ))


def main():
    channels = {
        "JackSucksAtLife": "https://www.youtube.com/user/JackSucksAtMinecraft",
        "JackSucksAtStuff": "https://www.youtube.com/channel/UCxLIJccyaRQDeyu6RzUsPuw",
        "Jack Massey Welsh": "https://www.youtube.com/channel/UCyktGLVQchOpvKgL7GShDWA",
        "JackSucksAtGeography": "https://www.youtube.com/channel/UCd15dSPPT-EhTXekA7_UNAQ",
        "JackSucksAtPopUpPirate": "https://www.youtube.com/channel/UCpCJRHoggwXQhuFbW4gjM_w",
        "JacksEpicYoutubeChannelFullOfFun...": "https://www.youtube.com/channel/UCF9R3Ln-u52vUdSO-pFdETw",
        "JackSucksAtClips": "https://www.youtube.com/channel/UCUXNOmIdsoyd5fh5TZHHO5Q",
        "No Context JackSuksAtLife": "https://www.youtube.com/channel/UCrZKnWgOaYTTc7sc1KsVXZw",
        "JackSucksAtEspañol": "https://www.youtube.com/channel/UCqx-my2rOoQuEOHKNNgNppw",
        "turd boi420": "https://www.youtube.com/channel/UCbu2qTa75eyjwCKOugX8F6A",
        "JACKSEPICYOUTUBECHANNEL...XX": "https://www.youtube.com/channel/UChLNLQ6r-aGrIFWo_1A9tKQ",
        "SamSmellsOfApricots": "https://www.youtube.com/user/SamSmellsOfApricots"
    }

    for channel_name, channel_page_url in channels.items():
        channel_id = get_channel_id_from_youtube_url(channel_page_url)
        video_ids = get_video_ids_from_channel_id(channel_id)
        video_list_responses = get_video_list_responses_from_ids(video_ids)

        total_views = sum(int(video_data["statistics"]["viewCount"]) for video_data in video_list_responses)
        total_time = sum(
            (isodate.parse_duration(video_data["contentDetails"]["duration"]) for video_data in video_list_responses),
            datetime.timedelta()
        )

        print(f"{channel_name} - total_seconds:{total_time.total_seconds()}, total_views:{total_views}")


if __name__ == "__main__":
    main()

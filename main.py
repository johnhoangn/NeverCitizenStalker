import discord
import re
import requests
import html5lib

bob_intents = discord.Intents.default()
bob_intents.messages=True
bob_intents.message_content=True
bot = discord.Client(intents=bob_intents)

def getElems(root, tagName):
    return root.getElementsByTagName(tagName)
def search(handle):
    output = ""

    with open("response.html", "w") as f:
        f.write(requests.get("https://robertsspaceindustries.com/en/citizens/" + handle).text)

    with open("response.html", "rb") as f:
        TreeBuilder = html5lib.getTreeBuilder("dom")
        parser = html5lib.HTMLParser(tree=TreeBuilder)
        dom = parser.parse(f)

        label_spans = [elem for elem in dom.getElementsByTagName("span") if elem.getAttribute("class") == "label"]
        for span in label_spans:
            for c in span.childNodes:
                if "Handle name" in c.data:
                    root = c.parentNode.parentNode.parentNode
                    output += "Username: " + getElems(root, "strong")[0].childNodes[0].data + '\n'
                    output += "Handle: " + getElems(root, "strong")[1].childNodes[0].data + '\n'
                elif "Enlisted" in c.data:
                    root = c.parentNode.parentNode
                    output += "Enlisted: " + getElems(root, "strong")[0].childNodes[0].data + '\n'
                elif "Fluency" in c.data:
                    root = c.parentNode.parentNode
                    fluencies = []
                    for text_nodes in getElems(root, "strong"):
                        for fluency in text_nodes.childNodes:
                            if len(fluency.data.strip()) > 0:
                                fluencies.append(fluency.data.strip())
                    output += "Fluencies: " + str(fluencies) + '\n'

                elif "UEE Citizen Record" in c.data:
                    root = c.parentNode.parentNode
                    output += "UserID: " + getElems(root, "strong")[0].childNodes[0].data + '\n'

        title_spans = [elem for elem in dom.getElementsByTagName("span") if elem.getAttribute("class") == "title"]
        for span in title_spans:
            for c in span.childNodes:
                text = c._get_wholeText()
                if "Main org" in text:
                    root = c.parentNode.parentNode
                    output += "Main Org: " + getElems(root, "a")[1].childNodes[0].data + '\n'

    return output


@bot.event
async def on_message(message):
    message_body = message.content
    if "!getbob" in message_body or "!bob" in message_body:
        try:
            name = message_body.split()[1]
            output = search(name)
            await message.channel.send(output)
        except:
            await message.channel.send("User {} not found dumbass")

with open(".SECRET") as f:
    bot.run(f.readline())

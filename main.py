import discord
import re
import requests
import html5lib
import json
import traceback


bob_intents = discord.Intents.default()
bob_intents.messages=True
bob_intents.message_content=True
bot = discord.Client(intents=bob_intents)


bobbusy = False


def getNotes(handle):
    handle = handle.strip()
    with open(r"notes.json", "r") as notes_file:
        notes = json.load(notes_file)
        notes_string = "**Notes:**" + '\n- '

        if handle in notes and len(notes[handle]) > 0:
            notes_string += "\n- ".join(notes[handle])
            notes_string += '\n'
        else:
            notes_string = "*No notes.*" + '\n'

    return notes_string


def setNote(handle, note):
    handle = handle.strip()
    with open(r"notes.json", "r") as old_notes:
        notes_data = json.load(old_notes)

        if handle in notes_data:
            handle_notes = notes_data[handle]
            handle_notes.append(note)
        else:
            handle_notes = list()
            handle_notes.append(note)
            notes_data[handle] = handle_notes

    with open(r"notes.json", "w") as notes_file:
        notes_file.write(json.dumps(notes_data, indent=2))


def deleteNote(handle, index):
    handle = handle.strip()
    with open(r"notes.json", "r") as old_notes:
        notes_data = json.load(old_notes)
        del notes_data[handle][int(index)]

    with open(r"notes.json", "w") as notes_file:
        notes_file.write(json.dumps(notes_data, indent=2))


def clearNotes(handle):
    handle = handle.strip()
    with open(r"notes.json", "r") as old_notes:
        notes_data = json.load(old_notes)
        del notes_data[handle]

    with open(r"notes.json", "w") as notes_file:
        notes_file.write(json.dumps(notes_data, indent=2))


def getElems(root, tagName):
    return root.getElementsByTagName(tagName)


def getPage(handle):
    url = "https://robertsspaceindustries.com/en/citizens/" + handle
    if requests.get(url).status_code != 200:
        return 404

    with open("response.html", "w") as f:
        f.write(requests.get(url).text)

    return 200


def exists(handle):
    return getPage(handle) == 200


def searchBob(handle):
    handle = handle.strip()
    output = ""

    if getPage(handle) != 200:
        return None

    with open("response.html", "rb") as f:
        TreeBuilder = html5lib.getTreeBuilder("dom")
        parser = html5lib.HTMLParser(tree=TreeBuilder)
        dom = parser.parse(f)

        label_spans = [elem for elem in dom.getElementsByTagName("span") if elem.getAttribute("class") == "label"]
        for span in label_spans:
            for c in span.childNodes:
                if "Handle name" in c.data:
                    root = c.parentNode.parentNode.parentNode
                    output += "**U/H:** " + getElems(root, "strong")[0].childNodes[0].data + "/" + getElems(root, "strong")[1].childNodes[0].data + '\n'

                elif "Enlisted" in c.data:
                    root = c.parentNode.parentNode
                    output += "**Enlisted:** " + getElems(root, "strong")[0].childNodes[0].data + '\n'

                elif "Fluency" in c.data:
                    root = c.parentNode.parentNode
                    fluencies = []

                    for text_nodes in getElems(root, "strong"):
                        for fluency_node in text_nodes.childNodes:
                            fluency_list = fluency_node.data.split()
                            if len(fluency_list) > 0:
                                for fluency in fluency_list:
                                    fluencies.append(re.sub(",", "", fluency.split()[0]))

                    output += "**Fluencies:** " + '\n- '
                    output += '\n- '.join(fluencies)

                    output += '\n'

                elif "UEE Citizen Record" in c.data:
                    root = c.parentNode.parentNode
                    citrec = getElems(root, "strong")[0].childNodes[0].data
                    if citrec == "n/a":
                        output += "*Not registered with UEE.*" + '\n'
                    else:
                        output += citrec + '\n'

        title_spans = [elem for elem in dom.getElementsByTagName("span") if elem.getAttribute("class") == "title"]

        try:
            for span in title_spans:
                for c in span.childNodes:
                    text = c._get_wholeText()
                    if "Main org" in text:
                        root = c.parentNode.parentNode
                        output += "Main Org: [" + getElems(root, "a")[1].childNodes[0].data + "](https://robertsspaceindustries.com/en" + getElems(root, "a")[1].childNodes[0].get('href') + ")\n"
        except:
            output += "*Not in an organization.*" + '\n'

        output += getNotes(handle) + '\n'

    return output

def searchOrg(orgName):
    output = ""

    with open("response.html", "w") as f:
        f.write(requests.get("https://robertsspaceindustries.com/en/community/orgs/listing?sort=default&search=" + orgName).text)
        
    with open("response.html", "rb") as f:
        TreeBuilder = html5lib.getTreeBuilder("dom")
        parser = html5lib.HTMLParser(tree=TreeBuilder)
        dom = parser.parse(f)

        orgSearchBox = [elem for elem in dom.getElementsByTagName("span") if elem.getAttribute("class") == "orgs-listing search"][0]
        for orgCell in orgSearchBox.childNodes:
            orgCellHrefData = orgCell[0].get('href')
            orgCellFullName = orgCell[0][0][1].data
            if orgCellFullName == orgName:
                output += "Org Link: https://robertsspaceindustries.com/en" + orgCellHrefData + '\n'

            f.write(requests.get("https://robertsspaceindustries.com/en" + orgCellHrefData).text)
            with open("response.html", "rb") as f:
                TreeBuilder = html5lib.getTreeBuilder("dom")
                parser = html5lib.HTMLParser(tree=TreeBuilder)
                dom = parser.parse(f)

                logo = [elem for elem in dom.getElementsByTagName("div") if elem.getAttribute("class") == "logo noshadow"]
                output += logo[0].get('src') + '\n'
                output += "Members: " + logo[1].data.replace(" members", "") + '\n'

                mottoSpans = [elem for elem in dom.getElementsByTagName("span") if elem.getAttribute("class") == "body markitup-text"]
                output += "Motto: "
                for span in mottoSpans:
                    for c in span.childNodes:
                        if c.nodeType == c.TEXT_NODE:
                            output += c.data.strip() + ' '

                output += '\n'

    return output


@bot.event
async def on_message(message):
    global bobbusy
    if bobbusy:
        return
    bobbusy = True

    message_body = message.content
    name = None
    command = None

    if "!bob" not in message_body:
        bobbusy = False
        return

    try:
        name = message_body.split()[2].strip().lower()
        command = message_body.split()[1].strip()
    except:
        name = message_body.split()[1].strip().lower()

    try:
        if " help" in message_body:
            await message.channel.send("Subcommands:\n- note <name> <msg> \n- dnote <name> <note#> \n- clearnotes <name>\n- org")
            bobbusy = False
            return

        if " org" in message_body:
            try:
                name = message_body.split()[1]
                output = searchOrg(name)
                await message.channel.send(output)
            except:
                await message.channel.send("Org {} not found")

            bobbusy = False
            return

        if command != None and len(command) > 0:
            if command == "note":
                if not exists(name):
                    await message.channel.send("No user by: " + name)
                    bobbusy = False
                    return

                setNote(name, ' '.join(message_body.split()[3:]))
                await message.channel.send("Set note for " + name + '\n' + ' '.join(message_body.split()[3:]))

            elif command == "dnote":
                index = message_body.split()[3]
                deleteNote(name, index)
                await message.channel.send("Deleted note #" + index)

            elif command == "clearnotes":
                clearNotes(name)
                await message.channel.send("Deleted all notes.")

            else:
                await message.channel.send("Bob no understand!")

        else:
            if not exists(name):
                await message.channel.send("No user by: " + name)
                bobbusy = False
                return

            output = search(name)
            await message.channel.send(output)

    except Exception as e:
        await message.channel.send("Bob error.")
        traceback.print_exc()

    bobbusy = False

with open(".SECRET") as f:
    bot.run(f.readline())

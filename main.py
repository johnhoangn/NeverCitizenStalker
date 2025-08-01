import discord
import re
import requests
import html5lib
import json
import traceback


# FUTURE DEVELOPMENT:
# USE 'dir(object)' TO EXPLORE ITS MEMBERS.


bob_intents = discord.Intents.default()
bob_intents.messages=True
bob_intents.message_content=True
bot = discord.Client(intents=bob_intents)


bobbusy = False


def get_notes(handle):
    handle = handle.strip()
    with open(r"notes.json", "r") as notes_file:
        notes = json.load(notes_file)
        notes_string = ""

        if handle in notes and len(notes[handle]) > 0:
            notes_string = '- '
            notes_string += "\n- ".join(notes[handle])
            notes_string += '\n'

    return notes_string


def set_note(handle, note):
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


def delete_note(handle, index):
    handle = handle.strip()
    with open(r"notes.json", "r") as old_notes:
        notes_data = json.load(old_notes)
        del notes_data[handle][int(index)]

    with open(r"notes.json", "w") as notes_file:
        notes_file.write(json.dumps(notes_data, indent=2))


def clear_notes(handle):
    handle = handle.strip()
    with open(r"notes.json", "r") as old_notes:
        notes_data = json.load(old_notes)
        del notes_data[handle]

    with open(r"notes.json", "w") as notes_file:
        notes_file.write(json.dumps(notes_data, indent=2))


def get_elems(root, tagName):
    return root.getElementsByTagName(tagName)


def get_page(handle):
    url = "https://robertsspaceindustries.com/en/citizens/" + handle
    if requests.get(url).status_code != 200:
        return 404

    with open("response.html", "w") as f:
        f.write(requests.get(url).text)

    return 200


def exists(handle):
    return get_page(handle) == 200


def search_bob(handle):
    handle = handle.strip()
    block = discord.Embed()

    #if get_page(handle) != 200:
    #    return None

    with open("response.html", "rb") as f:
        TreeBuilder = html5lib.getTreeBuilder("dom")
        parser = html5lib.HTMLParser(tree=TreeBuilder)
        dom = parser.parse(f)

        user_thumbnail = "https://robertsspaceindustries.com/" + [elem for elem in dom.getElementsByTagName("div") if elem.getAttribute("class") == "thumb"][0].childNodes[1].getAttribute("src")
        user_name = ""
        user_handle = ""
        citizen_recod = ""
        main_organization_name = ""
        main_organization_uri = ""
        notes = get_notes(handle)
        fluencies = []

        label_spans = [elem for elem in dom.getElementsByTagName("span") if elem.getAttribute("class") == "label"]
        for span in label_spans:
            for c in span.childNodes:
                if "Handle name" in c.data:
                    root = c.parentNode.parentNode.parentNode
                    user_name = get_elems(root, "strong")[0].childNodes[0].data
                    user_handle = get_elems(root, "strong")[1].childNodes[0].data

                elif "Enlisted" in c.data:
                    root = c.parentNode.parentNode
                    enlisted = get_elems(root, "strong")[0].childNodes[0].data

                elif "Fluency" in c.data:
                    root = c.parentNode.parentNode

                    for text_nodes in get_elems(root, "strong"):
                        for fluency_node in text_nodes.childNodes:
                            fluency_list = fluency_node.data.split()
                            if len(fluency_list) > 0:
                                for fluency in fluency_list:
                                    fluencies.append(re.sub(",", "", fluency.split()[0]))

                elif "UEE Citizen Record" in c.data:
                    root = c.parentNode.parentNode
                    citizen_record = get_elems(root, "strong")[0].childNodes[0].data

        title_spans = [elem for elem in dom.getElementsByTagName("span") if elem.getAttribute("class") == "title"]

        try:
            for span in title_spans:
                for c in span.childNodes:
                    text = c._get_wholeText()
                    if "Main org" in text:
                        root = c.parentNode.parentNode
                        main_organization_name = get_elems(root, "a")[1].childNodes[0].data
                        main_organization_uri = "https://robertsspaceindustries.com/en" + get_elems(root, "a")[1].getAttribute('href')
        except:
            traceback.print_exc()

        block.title = f"{user_handle}"
        block.description = f"aka {user_name}" if user_handle != user_name else None
        block.set_thumbnail(url = user_thumbnail)
        block.description = "https://robertsspaceindustries.com/en/citizens/{handle}"
        
#        if citizen_record != "n/a":
#            block.add_field(name = "UEEID", value = f"{citizen_record}")
#        else:
#            block.add_fied("UEEID", value = "*Not registered with UEE.*")

        if main_organization_name != "":
            block.add_field(name = "*Main Organization*", value = f"[{main_organization_name}](https://robertsspaceindustries.com/en{main_organization_uri})")
        else:
            block.add_field(name = "*Main Organization*", value = "Has no friends.")

        block.add_field(name = "*Fluencies*", value = '- ' + '- \n'.join(fluencies))

    return block, notes

def search_org(orgName):
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

        if " org " in message_body:
            try:
                name = message_body.split()[1]
                output = search_org(name)
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

                set_note(name, ' '.join(message_body.split()[3:]))
                await message.channel.send("Set note for " + name + '\n' + ' '.join(message_body.split()[3:]))

            elif command == "dnote":
                index = message_body.split()[3]
                delete_note(name, index)
                await message.channel.send("Deleted note #" + index)

            elif command == "clearnotes":
                clear_notes(name)
                await message.channel.send("Deleted all notes.")

            else:
                await message.channel.send("Bob no understand!")

        else:
            if not exists(name):
                await message.channel.send("No user by: " + name)
                bobbusy = False
                return

            block, notes = search_bob(name)

            await message.channel.send(embed=block)
            await message.channel.send("**Notes:**\n" + notes)

    except Exception as e:
        await message.channel.send("Bob error.")
        traceback.print_exc()

    bobbusy = False

#search_bob("TwoHanded")

with open(".SECRET") as f:
    bot.run(f.readline())


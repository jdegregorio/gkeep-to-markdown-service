import json

def escape_control_chars(s):
    return s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


test = "{\n\"note_title\": \"AI as Common Language Interface\",\n\"note_type\": \"idea\",\n\"note_rewrite\": \"In the modern digital landscape, we are inundated with a multitude of tools, each with its unique user interface. This often necessitates frequent context switching and data transfer between tools to fully harness their combined capabilities. However, advancements in AI and large language models present a solution to this issue. They can serve as a common programmatic interface, managing and switching contexts on behalf of the user. This not only reduces the cognitive load of learning and operating multiple interfaces but also streamlines manual actions across different platforms. \n\nThe benefits of this approach are manifold:\n- **Deep Integration**: AI provides a common language interface, enabling users to leverage the combined power of multiple tools.\n- **Improved Communication**: Within a single tool, AI can enhance the way users communicate their intent to the software. For instance, while working with Excel, users may struggle to visualize or interpret their data. AI, acting as a digital peer, can assist in brainstorming the best ways to utilize the software and data.\n- **Task Automation**: Tasks that were previously time-consuming, such as entering a grocery list into Instacart, can now be accomplished almost instantaneously thanks to AI.\",\n\"note_topics\": [\"AI\", \"Language Models\", \"User Interface\", \"Automation\", \"Task Management\"]\n}"
test = escape_control_chars(test)
json.loads(test)

import re

test = "{\n\"note_title\": \"AI as Common Language Interface\",\n\"note_type\": \"idea\",\n\"note_rewrite\": \"In the modern digital landscape, we are inundated with a multitude of tools, each with its unique user interface. This often necessitates frequent context switching and data transfer between tools to fully harness their combined capabilities. However, advancements in AI and large language models present a solution to this issue. They can serve as a common programmatic interface, managing and switching contexts on behalf of the user. This not only reduces the cognitive load of learning and operating multiple interfaces but also streamlines manual actions across different platforms. \n\nThe benefits of this approach are manifold:\n- **Deep Integration**: AI provides a common language interface, enabling users to leverage the combined power of multiple tools.\n- **Improved Communication**: Within a single tool, AI can enhance the way users communicate their intent to the software. For instance, while working with Excel, users may struggle to visualize or interpret their data. AI, acting as a digital peer, can assist in brainstorming the best ways to utilize the software and data.\n- **Task Automation**: Tasks that were previously time-consuming, such as entering a grocery list into Instacart, can now be accomplished almost instantaneously thanks to AI.\",\n\"note_topics\": [\"AI\", \"Language Models\", \"User Interface\", \"Automation\", \"Task Management\"]\n}"

def custom_parser(string_object):
    # regular expression patterns for the keys and values
    pattern = r'"(note_title|note_type|note_rewrite|note_topics)":(.*?)(?="note_title"|"note_type"|"note_rewrite"|"note_topics"|}$)'
    
    matches = re.findall(pattern, string_object, re.DOTALL)
    dict_obj = {}
    
    for key, value in matches:
        # remove leading and trailing spaces and quotes
        value = value.strip(" \n\"")
        
        # if it's an array (note_topics), convert to list
        if key == "note_topics":
            value = value.strip("[]").split(",")
            value = [item.strip(" \"") for item in value]
        
        dict_obj[key] = value
    
    return dict_obj

out = custom_parser(test)
out['note_rewrite']


# test = test.replace("\\", "\\\\")
test
test_dumped = json.dumps(test)
output = json.loads(test_dumped, )


test = "{\n\"note_title\": \"Software Exploration Agents\",\n\"note_type\": \"idea\",\n\"note_rewrite\": \"The note discusses the concept of **software exploration agents**. These are agents that request your code to test, run, and fully comprehend all of its features. They operate similarly to a human exploring new software, exhaustively interacting with every feature. Once these agents have a thorough understanding of the software's functionality, they are capable of constructing examples and guides.\",\n\"note_topics\": [\"Software Exploration\", \"Agents\", \"Code Testing\", \"Documentation\"]\n}"
json.loads(test)


test = "{\n\"note_title\": \"Day Plan\",\n\"note_type\": \"idea\",\n\"note_rewrite\": \"**Tasks:**\\n- Store items in the attic\\n- Prepare Stella's passport\\n\\n**Schedule:**\\n- 10:00-11:30: Wake Window\\n  - Practice sitting up\\n  - Tummy time\\n  - Reading books\\n  - Singing songs\\n\\n- 11:30 - 1:00PM: Nap and preparation for lake visit\\n  - Pack stroller\\n  - Prepare bottle\\n  - Pack blanket\\n  - Pack toys\\n  - Pack milk\\n  - Pack hot water for warming milk\\n  - Pack hat(s)\\n\\n- 1:00 - 3:30: Walk around Greenlake\\n\\n- 3:30 - 4:30: Nap\",\n\"note_topics\": [\"Day Planning\", \"Task Management\", \"Scheduling\"]\n}"
json.loads(test)
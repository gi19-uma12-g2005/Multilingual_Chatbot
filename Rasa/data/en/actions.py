from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="দুঃখিত, আমি বুঝতে পারিনি। সাহায্যের জন্য আমাদের support@institution.edu এই ইমেইলে যোগাযোগ করুন। দয়া করে আবার বলুন।")
        return []

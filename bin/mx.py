import sys
import os
from datetime import datetime, timedelta
import json
import traceback
import requests
from requests.compat import urljoin

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from splunklib.searchcommands import dispatch, StreamingCommand, Configuration, Option, validators
from splunklib.binding import HTTPError

CACHE_DATE_FIELD = "cache_entry_date"
CACHE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
BASE_URL = "https://mxtoolbox.com/api/v1/lookup"

@Configuration()
class MXToolboxAPI(StreamingCommand):
    opt_user = Option(name="user", default="mxt_default_api", require=False)
    opt_nocache = Option(name="nocache", default=False, require=False, validate=validators.Boolean())
    opt_action = Option(name="action", default=None, require=True)

    field_key = None
    cache_kv_name = "mx_cache"
    api_key = None
    cache_kv = None
    search_time = datetime.now()
    cache_expiration = None

    def manage_error(self,error):
        self.logger.error(traceback.format_exc())
        self.write_error("ERROR Unexpected error: {}".format(error))

    def init_cache(self, collection_name):
        try:
            if collection_name in self.service.kvstore:
                self.cache_kv = self.service.kvstore[collection_name]
            else:
                self.write_warning("WARNING: Cache KV Store not available. Escaping cache related actions.")
                self.opt_nocache = True
        except Exception as ex:
            self.manage_error(ex)
            self.write_warning("WARNING: Cache KV Store not available. Escaping cache related actions.")
            self.opt_nocache = True

    def cache_search(self, key):
        if key is not None:
            try:
                result = self.cache_kv.data.query_by_id(key)
                return result
            except Exception as ex:
                self.manage_error(ex)
        else:
            return None

    def update_cache(self, key, entry):
        if self.cache_kv is not None and key is not None and entry is not None:
            entry[CACHE_DATE_FIELD] = self.search_time.strftime(CACHE_DATE_FORMAT)
            entry["_key"] = key
            entry_json = json.dumps(entry)

            try:
                self.cache_kv.data.update(key, entry_json)
            except HTTPError as ex:
                if ex.status == 404:
                    try:
                        self.cache_kv.data.insert(entry_json)
                    except HTTPError as ex:
                        if ex.status == 409:
                            pass
                        else:
                            self.manage_error(ex)

    def is_expired(self, record_date_str):
        try:
            cache_date = datetime.strptime(record_date_str, CACHE_DATE_FORMAT)
            cache_freshness = self.search_time - cache_date
            if cache_freshness > self.cache_expiration:
                return True
            return False
        except TypeError:
            return True

    @staticmethod
    def flatten_json(y):
        out = {}
        def flatten(x, name=''):
            if isinstance(x, dict):
                for a in x:
                    flatten(x[a], name + a + '_')
            else:
                out[name[:-1]] = x
        flatten(y)
        return out
    
    @staticmethod
    def reformat_json(event):
        failed = event.get("Failed", [])
        warnings = event.get("Warnings", [])
        errors = event.get("Errors", [])
        passed = event.get("Passed", [])
        timeouts = event.get("Timeouts", [])
        transcripts = event.get("Transcript", [])
        infos = event.get("Information", [])

        result = {
            "Domain": [],
            "Control": [],
            "Name": [],
            "Result": [],
            "Info": [],
            "AdditionalInfo": [],
            "Timeout": [],
            "MxReputation": [],
            "RelatedIP": [],
            "ReportingNameServer": []
        }
        sep = ". "

        for obj in transcripts:
            result["Domain"].append(event.get("CommandArgument"))
            result["Control"].append(event.get("Command").title())
            result["Name"].append(obj.get("Name"))
            result["Result"].append("Transcript")
            result["Info"].append(obj.get("Info", "-"))
            result["Timeout"].append("N")
            result["MxReputation"].append(event.get("MxRep", "-"))
            result["RelatedIP"].append(event.get("RelatedIP", "-"))
            result["ReportingNameServer"].append(event.get("ReportingNameServer", "-"))
            adInfo = "-"
            if len(obj.get("AdditionalInfo", [])) != 0 and obj.get("AdditionalInfo")[0] != "":
                adInfo = sep.join(obj.get("AdditionalInfo"))
            result["AdditionalInfo"].append(adInfo)
        
        for obj in timeouts:
            result["Domain"].append(event.get("CommandArgument"))
            result["Control"].append(event.get("Command").title())
            result["Name"].append(obj.get("Name"))
            result["Result"].append("Timeout")
            result["Info"].append(obj.get("Info", "-"))
            result["Timeout"].append("Y")
            result["MxReputation"].append(event.get("MxRep", "-"))
            result["RelatedIP"].append(event.get("RelatedIP", "-"))
            result["ReportingNameServer"].append(event.get("ReportingNameServer", "-"))
            adInfo = "-"
            if len(obj.get("AdditionalInfo", [])) != 0 and obj.get("AdditionalInfo")[0] != "":
                adInfo = sep.join(obj.get("AdditionalInfo"))
            result["AdditionalInfo"].append(adInfo)
        
        for obj in infos:
            result["Domain"].append(event.get("CommandArgument"))
            typ = obj.get("Type", "") + " - " if obj.get("Type", "") != "" else "" 
            result["Control"].append(typ + event.get("Command").title())
            result["Name"].append(obj.get("Domain Name"))
            result["Result"].append("Info")
            result["Info"].append(obj.get("IP Address", "-"))
            result["Timeout"].append("N")
            result["MxReputation"].append(event.get("MxRep", "-"))
            result["RelatedIP"].append(event.get("RelatedIP", "-"))
            result["ReportingNameServer"].append(event.get("ReportingNameServer", "-"))
            adInfo = "-"
            if len(obj.get("AdditionalInfo", [])) != 0 and obj.get("AdditionalInfo")[0] != "":
                adInfo = sep.join(obj.get("AdditionalInfo"))
            result["AdditionalInfo"].append(adInfo)

        for obj in failed:
            result["Domain"].append(event.get("CommandArgument"))
            result["Control"].append(event.get("Command").title())
            result["Name"].append(obj.get("Name"))
            result["Result"].append("Failed")
            result["Info"].append(obj.get("Info", "-"))
            result["Timeout"].append("N")
            result["MxReputation"].append(event.get("MxRep", "-"))
            result["RelatedIP"].append(event.get("RelatedIP", "-"))
            result["ReportingNameServer"].append(event.get("ReportingNameServer", "-"))
            adInfo = "-"
            if len(obj.get("AdditionalInfo", [])) != 0 and obj.get("AdditionalInfo")[0] != "":
                adInfo = sep.join(obj.get("AdditionalInfo"))
            result["AdditionalInfo"].append(adInfo)
        for obj in warnings:
            result["Domain"].append(event.get("CommandArgument"))
            result["Control"].append(event.get("Command").title())
            result["Name"].append(obj.get("Name"))
            result["Result"].append("Warning")
            result["Info"].append(obj.get("Info", "-"))
            result["Timeout"].append("N")
            result["MxReputation"].append(event.get("MxRep", "-"))
            result["RelatedIP"].append(event.get("RelatedIP", "-"))
            result["ReportingNameServer"].append(event.get("ReportingNameServer", "-"))
            adInfo = "-"
            if len(obj.get("AdditionalInfo", [])) != 0 and obj.get("AdditionalInfo")[0] != "":
                adInfo = sep.join(obj.get("AdditionalInfo"))
            result["AdditionalInfo"].append(adInfo)
        for obj in errors:
            result["Domain"].append(event.get("CommandArgument"))
            result["Control"].append(event.get("Command").title())
            result["Name"].append(obj.get("Name"))
            result["Result"].append("Error")
            result["Info"].append(obj.get("Info", "-"))
            result["Timeout"].append("N")
            result["MxReputation"].append(event.get("MxRep", "-"))
            result["RelatedIP"].append(event.get("RelatedIP", "-"))
            result["ReportingNameServer"].append(event.get("ReportingNameServer", "-"))
            adInfo = "-"
            if len(obj.get("AdditionalInfo", [])) != 0 and obj.get("AdditionalInfo")[0] != "":
                adInfo = sep.join(obj.get("AdditionalInfo"))
            result["AdditionalInfo"].append(adInfo)
        for obj in passed:
            result["Domain"].append(event.get("CommandArgument"))
            result["Control"].append(event.get("Command", "-").title())
            result["Name"].append(obj.get("Name", "-"))
            result["Result"].append("Passed")
            result["Info"].append(obj.get("Info", "-"))
            result["Timeout"].append("N")
            result["MxReputation"].append(event.get("MxRep", "-"))
            result["RelatedIP"].append(event.get("RelatedIP", "-"))
            result["ReportingNameServer"].append(event.get("ReportingNameServer", "-"))
            adInfo = "-"
            if len(obj.get("AdditionalInfo", [])) != 0 and obj.get("AdditionalInfo")[0] != "":
                adInfo = sep.join(obj.get("AdditionalInfo"))
            result["AdditionalInfo"].append(adInfo)

        return result

    def api_request(self, domain):
        headers = {'Authorization': self.api_key}
        url = BASE_URL + "/" + self.opt_action + "/" + domain
        response = requests.get(url, headers=headers)

        if response.ok:
            body_dict = response.json()
            return self.reformat_json(body_dict)
        else:
            response.raise_for_status()

    def prepare(self):
        if len(self.fieldnames)==1:
            self.field_key = self.fieldnames[0]
            try:
                storage_passwords = self.service.storage_passwords
                self.api_key = [k for k in storage_passwords if k.content.get('username')==self.opt_user][0].content.get('clear_password')
                if self.api_key is None:
                    raise IndexError

                conf_cache_validity_interval_minutes = int(self.service.confs["mxt_settings"]["cache"]["validity_interval_minutes"])
                self.cache_expiration = timedelta(minutes=conf_cache_validity_interval_minutes)

                self.init_cache(self.opt_action + "_cache")
            except IndexError as ex:
                self.logger.error(ex)
                self.write_error("The specified API label does not exist. Please spellcheck or configure it.")
            except Exception as e:
                self.logger.error(e)
                self.write_error("ERROR in preparing: {}".format(e))
                sys.exit(1)
        else:
           self.write_error("At least one field name required for key values")
           exit(1)

    def stream(self, records):
        try:
            for record in records:
                if self.field_key in list(record.keys()) and record.get(self.field_key,None) is not "":
                    result = None
                    if self.opt_nocache:
                        result = self.api_request(record.get(self.field_key))
                        self.update_cache(record.get(self.field_key), result)
                    else:
                        result = self.cache_search(record.get(self.field_key))
                        if result is None or self.is_expired(result.get(CACHE_DATE_FIELD)):
                            result = self.api_request(record.get(self.field_key))
                            self.update_cache(record.get(self.field_key), result)
                            pass
                    if result is not None:
                        record.update(result)
                yield record
        except Exception as err:
            self.logger.error(err)
            self.write_error("ERROR in STREAM: {}".format(err))

if __name__ == "__main__":
    dispatch(MXToolboxAPI, sys.argv, sys.stdin, sys.stdout, __name__)
#!/usr/bin/env python2

from copy import copy


def GenVariantKey(incoming_headers):
    """\
Given stored-headers, a set of headers from a stored response, a normalised variant-key for that message can be generated by:

1. Let variant-key-header be a string, the result of selecting all field-values of stored-headers whose field-name is "Variant-Key" and joining them with a comma (",").
2. Remove all whitespace from variant-key-header.
3. Return variant-key-header.
"""
    variant_key_header = ",".join(incoming_headers.get("Variant-Key", []))
    variant_key_header.replace(" ", "")
    variant_key_header.replace("    ", "")
    return variant_key_header


def CacheBehaviour(incoming_request, selected_responses):
    """\
They do so by running this algorithm (or its functional equivalent) upon receiving a request, incoming-request:

1. Let selected-responses be a list of the stored responses suitable for reuse as defined in {{!RFC7234}} Section 4, excepting the requirement to calculate a secondary cache key.
2. If selected-responses is empty, return an empty list.
3. Order selected-responses by the "Date" header field, most recent to least recent.
4. If the freshest (as per {{!RFC7234}}, Section 4.2) has one or more "Variants" header field(s):
   1. Select one member of selected_responses and let its "Variants" header field-value(s) be variants-header. This SHOULD be the most recent response, but MAY be from an older one as long as it is still fresh.
   2. Let sorted-variants be an empty list.
   3. For each variant in variants-header:
      1. If variant's field-name corresponds to the request header field identified by a content negotiation mechanism that the implementation supports:
         1. Let request-value be the field-value(s) associated with field-name in incoming-request.
         2. Let available-values be a list containing all available-value for variant.
         3. Let sorted-values be the result of running the algorithm defined by the content negotiation mechanism with request-value and available-values.
         4. Append sorted-values to sorted-variants.
                  
      At this point, sorted-variants will be a list of lists, each member of the top-level list corresponding to a variant-item in the Variants header field-value, containing zero or more items indicating available-values that are acceptable to the client, in order of preference, greatest to least.

   4. Let sorted-keys be the result of running Find Available Keys ({{find}}) on sorted-variants, an empty string and an empty list.
"""
    selected_responses.sort(dateSort)
    if not selected_responses:
        return []
    freshest_selected = selected_responses[0]
    variants_header = freshest_selected.get("variants", [])
    sorted_variants = []
    for variant in variants_header:
        field_name = variant[0]
        available_values = variant[1:]
        conneg_mechanism = SupportedConneg.get(field_name.lower(), None)
        if conneg_mechanism:
            request_value = incoming_request.get(field_name.lower(), [])
            sorted_values = conneg_mechanism(request_value, available_values)
            sorted_variants.append(sorted_values)
    sorted_keys = FindAvailableKeys(sorted_variants, "", [])
    return sorted_keys


def dateSort(a,b):
    return 1 # FIXME: sorting


def FindAvailableKeys(sorted_variants, key_stub="", possible_keys=[]):
    """\
Given sorted-variants, a list of lists, and key-stub, a string representing a partial key, and possible-keys, a list:

1. Let sorted-values be the first member of sorted-variants.
2. For each sorted-value in sorted-values:
   1. If key-stub is an empty string, let this-key be a copy of sorted-value.
   1. Otherwise:
      1. Let this-key be a copy of key-stub.
      2. Append a comma (",") to this-key.
      3. Append sorted-value to this-key.
   3. Let remaining-variants be a copy of all of the members of sorted-variants except the first.
   4. If remaining-variants is empty, append this-key to possible-keys.
   5. Otherwise, run Find Available Keys on remaining-variants, this-key and possible-keys.
3. Return possible-keys.
"""
    sorted_values = sorted_variants[0]
    for sorted_value in sorted_values:
        if key_stub:
            this_key = copy(key_stub) + "," + sorted_value
        else:
            this_key = sorted_value
        remaining_variants = copy(sorted_variants[1:])
        if not remaining_variants:
            possible_keys.append(this_key)
        else:
            FindAvailableKeys(remaining_variants, this_key, possible_keys)
    return possible_keys


def Accept(request_value, available_values):
    """\
To perform content negotiation for Accept given a request-value and available-values:

1. Let preferred-available be an empty list.
2. Let preferred-types be a list of the types in the request-value, ordered by their weight, highest to lowest, as per {{!RFC7231}} Section 5.3.2 (omitting any coding with a weight of 0). If "Accept" is not present or empty, preferred-types will be empty. If a type lacks an explicit weight, an implementation MAY assign one.
3. If preferred-types is empty, append "*/*".
4. For each preferred-type in preferred-types:
   1. If any member of available-values matches preferred-type, using the media-range matching mechanism specified in {{!RFC7231}} Section 5.3.2 (which is case-insensitive), append those members of available-values to preferred-available (preserving the precedence order implied by the media ranges' specificity).
5. Return preferred-available.
"""

    preferred_available = []
    preferred_types = request_value
    preferred_types.sort(qValSort)
    if not preferred_types:
        preferred_types.append("*/*")
    for preferred_type in preferred_types:
        matches = mediaRangeMatch(preferred_type, available_values)
        if matches:
            preferred_available.extend(matches)
    return preferred_available

def mediaRangeMatch(preferred_type, available_values):
    if preferred_type == "*/*":
        return available_values
    elif preferred_type[-2:] == "/*":
        _type = preferred_type[:2].lower()
        output = []
        for available_value in available_values:
            if available_value[:value.index("/")].lower() == _type:
                output.append(available_value)
        return output
    else:
        for available_value in available_values:
            if preferred_type.lower() == available_value.lower():
                return [available_value]


def AcceptEncoding(request_value, available_values):
    """\
To perform content negotiation for Accept-Encoding given a request-value and available-values:

1. Let preferred-available be an empty list.
2. Let preferred-codings be a list of the codings in the request-value, ordered by their weight, highest to lowest, as per {{!RFC7231}} Section 5.3.1 (omitting any coding with a weight of 0). If "Accept-Encoding" is not present or empty, preferred-codings will be empty. If a coding lacks an explicit weight, an implementation MAY assign one.
3. If "identity" is not a member of preferred-codings, append "identity".
4. Append "identity" to available-values.
5. For each preferred-coding in preferred-codings:
   1. If there is a case-insensitive, character-for-character match for preferred-coding in available-values, append that member of available-values to preferred-available.
6. Return preferred-available.
"""
    preferred_available = []
    preferred_codings = request_value
    preferred_codings.sort(qValSort)
    if not "identity" in preferred_codings:
        preferred_codings.append("identity")
    available_values.append("identity")
    for preferred_coding in preferred_codings:
        if preferred_coding.lower() in [av.lower() for av in available_values]:
            preferred_available.append(preferred_coding.lower())
    return preferred_available


def AcceptLanguage(request_value, available_values):
    """\
To perform content negotiation for Accept-Language given a request-value and available-values:

1. Let preferred-available be an empty list.
2. Let preferred-langs be a list of the language-ranges in the request-value, ordered by their weight, highest to lowest, as per {{!RFC7231}} Section 5.3.1 (omitting any language-range with a weight of 0). If a language-range lacks a weight, an implementation MAY assign one.
3. If the first member of available-values is not a member of preferred-langs, append it to preferred-langs (thus making it the default).
4. For each preferred-lang in preferred-langs:
   1. If any member of available-values matches preferred-lang, using either the Basic or Extended Filtering scheme defined in {{!RFC4647}} Section 3.3, append those members of available-values to preferred-available (preserving their order).
5. Return preferred-available.
"""
    preferred_available = []
    preferred_langs = request_value
    preferred_langs.sort(qValSort)
    if not available_values[0] in preferred_langs: # FIXME: IndexError
        preferred_langs.append(available_values[0])
    for preferred_lang in preferred_langs:
        matches = rfc4647Match(preferred_lang, available_values)
        if matches:
            preferred_available.extend(matches)
    return preferred_available

def rfc4647Match(preferred_lang, available_values):
    output = []
    for available_value in available_values:
        if preferred_lang.lower() == available_value.lower():
            output.append(available_value)
        else:
            prefix = available_value[:len(preferred_lang)]
            next_char = available_value[len(preferred_lang):len(preferred_lang)+1]
            if preferred_lang.lower() == prefix.lower() and next_char == "-":
                output.append(available_value)
    return output



def qValSort(a,b):
    # FIXME: sort by qval
    return 1


SupportedConneg = {
    'accept': Accept,
    'accept-encoding': AcceptEncoding,
    'accept-language': AcceptLanguage
}


def runTest(test):
    result = CacheBehaviour(test["request"], test["stored_responses"])
    outcome = "PASS" if result == test['expects'] else "FAIL"
    return "* %s %s  [%s]" % (outcome, test['name'], ", ".join(result))
    

if __name__ == "__main__":
    import json
    import sys
    for test_file in sys.argv[1:]:
        sys.stderr.write("Loading %s...\n" % test_file)
        test_fh = open(test_file)
        test_json = json.load(test_fh)
        test_fh.close()
        for test in test_json:
            print runTest(test)

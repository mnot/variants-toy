
# Variants Toy

This is a prototype implementation of the algorithms in [HTTP Representation Variants](https://mnot.github.io/I-D/variants/), and is expected to evolve with them.

Currently, it elides the header parsing, expecting the test data to contain pre-parsed header fields.

Run it like:

> python2 variants.py test_encoding_.json

or just:

> make

to run all tests.

The test format is a list of JSON objects, with the following members:

~~~ javascript
{
  "name": "test subject",               // A string that names the test 
  "expects": ["identity,en"],           // A list of normalised variant-ids that we expect to match
  "stored_responses": [                 // A list of HTTP responses in the cache.
    {                                   // Currently only the first is used.
      "variants": [                     // Header field name; must be lowercase
        ["Accept-Encoding", "gzip"],    // [field-name, field-value] tuples; any case for names
        ["Accept-Language", "en", "fr"]
      ],
      "variant-key": ["gzip,en"]        // Most responses will need both variants and variant-key
    }
  ],
  "request": {                          // The incoming request
    "accept-encoding": ["br"],          // Header field-names, field-values. Names need to be lc
    "accept-language": ["de"]           // Values are lists
  }
}
~~~


Regarding code quality - don't judge me.

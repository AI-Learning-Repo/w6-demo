# A2A client smoke tests
Install `pip install -r clients/requirements.txt` in the client environment. Start the current sellers on localhost ports 11001 and 11000 first. From repository root:

```
python clients/test_discovery.py
python clients/test_all.py --delay 10 --json
python clients/test_all.py --full --delay 20
```

Discovery uses no LLM. The default suite makes two sequential seller requests, the full suite four. No client LLM or API key is needed. Seller processes need their own Gemini key. Delays reduce bursts but cannot guarantee quota compliance. On quota failure, stop and follow provider retry guidance. Tests check completed tasks and expected amounts, not semantic correctness or order creation. Scripts are based on the validated notebook interface but have not been run against the live Colab servers.

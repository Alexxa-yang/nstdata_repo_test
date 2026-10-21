# Evidence and current implementation

Reviewed on 2026-10-21. The operator completed Markdown and HTML live acceptance; see VALIDATION.txt.

| Decision | Evidence | State |
| --- | --- | --- |
| Proposed package pin `nstdata-ai-crawl==0.1.1` | [Official package setup](https://github.com/nstdata-ai/crawl-py/blob/main/setup.py) | Source inspected; package installed locally |
| Async submission, ANY proxy, three formats, 30000ms | Owner-supplied Playground snippet | Received without credential or execution result |
| Poll `get_scrape_task_result` by task ID | [Official Python client](https://github.com/nstdata-ai/crawl-py/blob/main/nstdata_ai_crawl/client.py) | Mocked-transport source contract passed |
| Download referenced Markdown, HTML and Raw Data | [Official response models](https://github.com/nstdata-ai/crawl-py/blob/main/nstdata_ai_crawl/models.py) | Inline and lazy reference handling verified offline |
| Keep SDK base URL unchanged | Owner Playground example and official client source | SDK defaults to api.nstproxy.com; basic live Markdown/HTML acceptance passed |

The adapter submits once, queries at most 20 times and waits 2 seconds between
pending queries. Task and HTTP socket timeouts do not form a whole-run deadline.
No automatic resubmission occurs. The wrapper makes no recursive site-wide requests.
Raw Data is exported as bytes, without assuming an HTML encoding.

The [general Crawl reference](https://docs.nstdata.io/docs/crawl) contains synchronous
route examples that differ from the reviewed SDK. This draft follows the supplied
asynchronous SDK method rather than inferring a synchronous endpoint.

The supplied [API reference root](https://apidocs.nstdata.io/) currently presents
the Resell Service API. Its retrieved public navigation covers proxy zones, channels,
IP products, orders, regions and proxy generation; no Crawl group was visible.
The [proxy generation endpoint](https://apidocs.nstdata.io/32971197e0) uses Bearer
authorization. This is a separate API from Crawl's x-api-key authentication.
Its displayed example contains undefined parameters and no formal query schema;
no proxy management endpoint has been implemented in this repository.

The proposed second repository concerns Crawl proxy country selection. The models
show `ProxyDto.country`; arbitrary custom proxy hosts are not assumed supported.
No throughput, pricing, trial-credit or success-rate claims are made.

"use client";
import Head from "next/head";
import { useState } from "react";

export default function TechnicalOverview() {
  const [activeTab, setActiveTab] = useState("architecture");

  const components = [
    { id: "architecture", name: "System Architecture" },
    { id: "scraping", name: "Data Acquisition" },
    { id: "embedding", name: "Vectorization" },
    { id: "qdrant", name: "Vector DB" },
    { id: "inference", name: "LLM Inference" },
    { id: "api", name: "API Design" },
  ];

  return (
    <div className="min-h-screen relative z-10 bg-gradient-to-br from-gray-900 to-gray-800 text-gray-100">
      <Head>
        <title>Technical Architecture - Veritium</title>
        <meta
          name="description"
          content="Deep technical overview of Veritium's fact-checking system"
        />
      </Head>

      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="bg-gradient-to-r from-blue-400 to-purple-500 text-transparent bg-clip-text">
              Veritium
            </span>{" "}
            Technical Architecture
          </h1>
          <p className="text-gray-300 max-w-3xl mx-auto">
            Comprehensive technical documentation for Veritiums AI-powered fact
            verification system. Designed for developers, engineers, and
            technical stakeholders.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap justify-center gap-2 mb-10">
          {components.map((component) => (
            <button
              key={component.id}
              onClick={() => setActiveTab(component.id)}
              className={`px-4 py-2 rounded-lg transition-all ${
                activeTab === component.id
                  ? "bg-pink-500 text-white"
                  : "bg-gray-800 hover:bg-gray-700 text-gray-300"
              }`}
            >
              {component.name}
            </button>
          ))}
        </div>

        {/* Content Sections */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 p-6">
          {activeTab === "architecture" && <ArchitectureOverview />}
          {activeTab === "scraping" && <DataAcquisition />}
          {activeTab === "embedding" && <EmbeddingProcess />}
          {activeTab === "qdrant" && <VectorDatabase />}
          {activeTab === "inference" && <LLMInference />}
          {activeTab === "api" && <APIDesign />}
        </div>
      </main>

      <footer className="text-center py-8 text-gray-500 text-sm">
        <p>Veritium v1.2.0 | © {new Date().getFullYear()} Veritium Research</p>
        <p className="mt-2">
          System Status: <span className="text-green-500">Operational</span> |
          Uptime: 99.87%
        </p>
      </footer>
    </div>
  );
}

function ArchitectureOverview() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-blue-400">
        System Architecture
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">
            High-Level Architecture
          </h3>
          <div className="space-y-4">
            <div className="flex items-start">
              <div className="bg-blue-500 rounded-full w-6 h-6 flex items-center justify-center mr-3 mt-1 flex-shrink-0">
                <span className="text-xs">1</span>
              </div>
              <div>
                <h4 className="font-medium">Data Acquisition Layer</h4>
                <p className="text-gray-400 text-sm mt-1">
                  Distributed web scrapers collecting fact-checks from verified
                  sources
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="bg-blue-500 rounded-full w-6 h-6 flex items-center justify-center mr-3 mt-1 flex-shrink-0">
                <span className="text-xs">2</span>
              </div>
              <div>
                <h4 className="font-medium">Vectorization Pipeline</h4>
                <p className="text-gray-400 text-sm mt-1">
                  Sentence Transformer models for embedding generation
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="bg-blue-500 rounded-full w-6 h-6 flex items-center justify-center mr-3 mt-1 flex-shrink-0">
                <span className="text-xs">3</span>
              </div>
              <div>
                <h4 className="font-medium">Qdrant Vector Database</h4>
                <p className="text-gray-400 text-sm mt-1">
                  Cloud-hosted vector DB for efficient similarity search
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="bg-blue-500 rounded-full w-6 h-6 flex items-center justify-center mr-3 mt-1 flex-shrink-0">
                <span className="text-xs">4</span>
              </div>
              <div>
                <h4 className="font-medium">LLM Inference Engine</h4>
                <p className="text-gray-400 text-sm mt-1">
                  Mixtral-8x7B-Instruct-v0.1 via HuggingFace TGI
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">Key Metrics</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="text-3xl font-bold text-blue-400">--</div>
              <div className="text-gray-400 text-sm mt-1">
                Fact-Checks Indexed
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="text-3xl font-bold text-green-400">384</div>
              <div className="text-gray-400 text-sm mt-1">
                Embedding Dimensions
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="text-3xl font-bold text-purple-400">46.7B</div>
              <div className="text-gray-400 text-sm mt-1">Model Parameters</div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="text-3xl font-bold text-yellow-400">--</div>
              <div className="text-gray-400 text-sm mt-1">
                Avg Response Time
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
        <h3 className="text-xl font-semibold mb-4">Technology Stack</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <TechStackItem name="Python" version="3.13.5" />
          <TechStackItem name="Qdrant" version="1.7.0" />
          <TechStackItem name="Sentence Transformers" version="2.2.2" />
          <TechStackItem name="Mixtral-8x7B" version="0.1" />
          <TechStackItem name="FastAPI" version="0.109.0" />
          <TechStackItem name="Docker" version="24.0" />
          <TechStackItem name="Redis" version="7.0" />
          <TechStackItem name="Celery" version="5.3" />
          <TechStackItem name="HuggingFace TGI" version="1.4.1" />
        </div>
      </div>
    </div>
  );
}

function TechStackItem({ name, version }) {
  return (
    <div className="flex items-center bg-gray-800 p-3 rounded-lg">
      <div className="bg-gray-700 w-10 h-10 rounded-lg mr-3 flex items-center justify-center">
        <span className="font-bold">{name.charAt(0)}</span>
      </div>
      <div>
        <div className="font-medium">{name}</div>
        <div className="text-gray-400 text-sm">v{version}</div>
      </div>
    </div>
  );
}

function DataAcquisition() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-blue-400">
        Data Acquisition Pipeline
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">
            Web Scraping Infrastructure
          </h3>
          <ul className="space-y-3">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Distributed scraping with Scrapy and Celery</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Rotating residential proxies for IP rotation</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Browser fingerprint randomization using Playwright</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Exponential backoff retry strategy with jitter</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>CAPTCHA solving integration via 2Captcha API</span>
            </li>
          </ul>

          <div className="mt-6">
            <h4 className="font-medium mb-2">Scraping Rate Limits</h4>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-400">Max Requests</div>
                  <div className="text-lg">12 RPM/source</div>
                </div>
                <div>
                  <div className="text-sm text-gray-400">Concurrency</div>
                  <div className="text-lg">8 workers</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">Data Sources & Schemas</h3>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="py-2 px-3 text-left">Source</th>
                  <th className="py-2 px-3 text-left">Fact-Checks</th>
                  <th className="py-2 px-3 text-left">Update Freq.</th>
                  <th className="py-2 px-3 text-left">Schema Version</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-800">
                  <td className="py-3 px-3">Snopes</td>
                  <td className="py-3 px-3">1,250,000+</td>
                  <td className="py-3 px-3">Hourly</td>
                  <td className="py-3 px-3">v2.1</td>
                </tr>
                <tr className="border-b border-gray-800">
                  <td className="py-3 px-3">PolitiFact</td>
                  <td className="py-3 px-3">850,000+</td>
                  <td className="py-3 px-3">Every 2 hours</td>
                  <td className="py-3 px-3">v1.8</td>
                </tr>
                <tr className="border-b border-gray-800">
                  <td className="py-3 px-3">BoomLive</td>
                  <td className="py-3 px-3">620,000+</td>
                  <td className="py-3 px-3">Daily</td>
                  <td className="py-3 px-3">v1.5</td>
                </tr>
                <tr>
                  <td className="py-3 px-3">AltNews</td>
                  <td className="py-3 px-3">480,000+</td>
                  <td className="py-3 px-3">Daily</td>
                  <td className="py-3 px-3">v1.5</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="mt-6">
            <h4 className="font-medium mb-2">Data Schema</h4>
            <pre className="bg-gray-800 p-4 rounded-lg overflow-x-auto text-sm">
              {`FactCheckSchema {
  id: UUID
  source: string
  claim: string
  verdict: string
  explanation: string
  rating: string
  date_published: datetime
  url: string
  entities: List[string]
  categories: List[string]
  metadata: JSON
  vector: List[float] (768 dimensions)
}`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

function EmbeddingProcess() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-blue-400">
        Vector Embedding Generation
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">Embedding Model</h3>

          <div className="mb-6">
            <div className="flex items-center mb-2">
              <div className="bg-purple-500 rounded-lg px-3 py-1 text-sm mr-3">
                Model
              </div>
              <div className="font-mono">
                sentence-transformers/all-mpnet-base-v2
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">Dimensions</div>
                <div className="text-lg">768</div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">Max Sequence</div>
                <div className="text-lg">384 tokens</div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">Model Size</div>
                <div className="text-lg">420 MB</div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">Pooling</div>
                <div className="text-lg">Mean Pooling</div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-2">Embedding Generation</h4>
            <pre className="bg-gray-800 p-4 rounded-lg overflow-x-auto text-sm">
              {`from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-mpnet-base-v2')

def generate_embedding(text: str) -> List[float]:
    # Preprocessing: Clean, normalize, truncate
    processed_text = preprocess(text)
    
    # Generate embedding
    embedding = model.encode(
        processed_text,
        convert_to_tensor=False,
        show_progress_bar=False,
        normalize_embeddings=True
    )
    
    return embedding.tolist()`}
            </pre>
          </div>
        </div>

        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">Embedding Pipeline</h3>

          <div className="space-y-6">
            <div>
              <h4 className="font-medium mb-2">Preprocessing Steps</h4>
              <ul className="space-y-2">
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">→</span>
                  <span>Unicode normalization (NFKC)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">→</span>
                  <span>
                    Lowercasing with case-sensitive entities preserved
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">→</span>
                  <span>Special character removal except punctuation</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">→</span>
                  <span>Token truncation to 380 tokens (512 BPE tokens)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">→</span>
                  <span>Language detection (English only)</span>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-2">Performance Metrics</h4>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-400">Throughput</div>
                    <div className="text-lg">1,240 docs/sec</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">P99 Latency</div>
                    <div className="text-lg">21 ms</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">Vector Size</div>
                    <div className="text-lg">3.07 KB</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">
                      Cosine Similarity
                    </div>
                    <div className="text-lg">0.87 avg</div>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium mb-2">Batch Processing</h4>
              <pre className="bg-gray-800 p-4 rounded-lg overflow-x-auto text-sm">
                {`# Using Celery for distributed processing
@app.task
def process_batch(batch_ids: List[str]):
    facts = FactCheck.objects.filter(id__in=batch_ids)
    texts = [f.claim + " " + f.explanation for f in facts]
    
    embeddings = model.encode(
        texts, 
        batch_size=128,
        convert_to_tensor=False
    )
    
    for fact, embedding in zip(facts, embeddings):
        fact.vector = embedding.tolist()
        fact.save()`}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function VectorDatabase() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-blue-400">
        Qdrant Vector Database
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">Database Configuration</h3>

          <div className="mb-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">Qdrant Version</div>
                <div className="text-lg">v1.7.0</div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">Cloud Tier</div>
                <div className="text-lg">Production-4XL</div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">Distance Metric</div>
                <div className="text-lg">Cosine</div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">Replication</div>
                <div className="text-lg">3x replica</div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-2">Collection Configuration</h4>
            <pre className="bg-gray-800 p-4 rounded-lg overflow-x-auto text-sm">
              {`from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(url="https://cluster.veritium.cloud")

client.create_collection(
    collection_name="fact_checks",
    vectors_config=models.VectorParams(
        size=768,  # Dimension of the vectors
        distance=models.Distance.COSINE
    ),
    optimizers_config=models.OptimizersConfigDiff(
        indexing_threshold=20000,
        memmap_threshold=100000
    ),
    shard_number=6,
    replication_factor=3,
    on_disk_payload=True
)`}
            </pre>
          </div>
        </div>

        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">Similarity Search</h3>

          <div className="space-y-6">
            <div>
              <h4 className="font-medium mb-2">Search Parameters</h4>
              <pre className="bg-gray-800 p-4 rounded-lg overflow-x-auto text-sm">
                {`def vector_search(query: str, top_k: int = 1) -> List[dict]:
    # Generate query embedding
    query_embedding = generate_embedding(query)
    
    # Perform search
    results = client.search(
        collection_name="fact_checks",
        query_vector=query_embedding,
        limit=top_k,
        with_payload=True,
        search_params=models.SearchParams(
            hnsw_ef=128,
            exact=False
        ),
        score_threshold=0.65
    )
    
    return [
        {
            "id": result.id,
            "score": result.score,
            "payload": result.payload
        }
        for result in results
    ]`}
              </pre>
            </div>

            <div>
              <h4 className="font-medium mb-2">Indexing Strategy</h4>
              <ul className="space-y-2">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>HNSW index with ef_construction=200, M=16</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Payload indexing for fast metadata filtering</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Quantization: Scalar 8-bit (for reduced memory)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Sharding: 6 shards for horizontal scaling</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function LLMInference() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-blue-400">
        LLM Inference Engine
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">Model Configuration</h3>

          <div className="mb-6">
            <div className="flex items-center mb-2">
              <div className="bg-yellow-500 rounded-lg px-3 py-1 text-sm mr-3">
                Model
              </div>
              <div className="font-mono">
                mistralai/Mixtral-8x7B-Instruct-v0.1
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">Parameters</div>
                <div className="text-lg">47B</div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">Context Window</div>
                <div className="text-lg">32K tokens</div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">Quantization</div>
                <div className="text-lg">GPTQ 4-bit</div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="text-sm text-gray-400">GPUs</div>
                <div className="text-lg">4x A100 80GB</div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-2">Inference Parameters</h4>
            <pre className="bg-gray-800 p-4 rounded-lg overflow-x-auto text-sm">
              {`inference_params = {
    "max_new_tokens": 512,
    "temperature": 0.7,
    "top_k": 50,
    "top_p": 0.95,
    "repetition_penalty": 1.15,
    "do_sample": True,
    "stop_sequences": ["</s>", "###"]
}`}
            </pre>
          </div>
        </div>

        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">Prompt Engineering</h3>

          <div>
            <h4 className="font-medium mb-2">Prompt Structure</h4>
            <pre className="bg-gray-800 p-4 rounded-lg overflow-x-auto text-sm">
              {`<s>[INST] 
You are a fact-checking assistant. Analyze the user's claim and 
the provided evidence to determine the claim's accuracy.

### CLAIM:
{user_query}

### EVIDENCE:
{retrieved_fact_check}

### INSTRUCTIONS:
1. Determine if the evidence directly addresses the claim
2. Extract the verdict from the evidence
3. Summarize the explanation in 2-3 sentences
4. Provide confidence score (0-100)
5. Return in JSON format

### RESPONSE FORMAT:
{
  "verdict": "true|false|misleading|unproven",
  "summary": "string",
  "confidence": 0-100,
  "sources": ["url1", ...]
}
[/INST]`}
            </pre>
          </div>

          <div className="mt-6">
            <h4 className="font-medium mb-2">Response Validation</h4>
            <pre className="bg-gray-800 p-4 rounded-lg overflow-x-auto text-sm">
              {`def validate_response(response: str) -> dict:
    try:
        data = json.loads(response)
        
        # Validate structure
        assert set(data.keys()) == {"verdict", "summary", "confidence", "sources"}
        assert data["verdict"] in VERDICT_TYPES
        assert 0 <= data["confidence"] <= 100
        assert isinstance(data["sources"], list)
        
        return data
    except (json.JSONDecodeError, AssertionError):
        return fallback_response()`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

function APIDesign() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-blue-400">API Design</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">REST API Endpoints</h3>

          <div className="mb-6">
            <h4 className="font-medium mb-2">POST /v1/factcheck</h4>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex justify-between text-sm mb-2">
                <div className="text-blue-400">Request</div>
                <div className="text-green-500">Response</div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <pre className="text-sm">
                  {`{
  "query": "COVID vaccines contain microchips",
  "top_k": 1,
  "detailed": false
}`}
                </pre>
                <pre className="text-sm">
                  {`{
  "id": "req_01HXYZ...",
  "verdict": "false",
  "summary": "No evidence...",
  "confidence": 98,
  "sources": ["https://..."],
  "evidence": {...},
  "processing_time": 142
}`}
                </pre>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-2">GET /v1/sources</h4>
            <div className="bg-gray-800 p-4 rounded-lg">
              <pre className="text-sm">
                {`[
  {
    "id": "snopes",
    "name": "Snopes",
    "url": "https://snopes.com",
    "factcheck_count": 1250000,
    "last_updated": "2025-08-16T14:32:10Z"
  },
  ...
]`}
              </pre>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 p-6 rounded-xl border border-gray-700">
          <h3 className="text-xl font-semibold mb-4">
            Performance & Monitoring
          </h3>

          <div className="space-y-6">
            <div>
              <h4 className="font-medium mb-2">Caching Strategy</h4>
              <ul className="space-y-2">
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">→</span>
                  <span>Redis cache for query embeddings (TTL: 24h)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">→</span>
                  <span>Vector search results cache (TTL: 12h)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">→</span>
                  <span>LLM response cache (TTL: 6h)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">→</span>
                  <span>Cache invalidation on data updates</span>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-2">Rate Limiting</h4>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-400">Free Tier</div>
                    <div className="text-lg">5 RPM</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">API Key</div>
                    <div className="text-lg">60 RPM</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">Burst</div>
                    <div className="text-lg">20 req/10s</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">Priority</div>
                    <div className="text-lg">Weighted QoS</div>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium mb-2">Monitoring Metrics</h4>
              <div className="flex flex-wrap gap-2">
                <span className="bg-gray-700 px-3 py-1 rounded-full text-sm">
                  Vector Search Latency
                </span>
                <span className="bg-gray-700 px-3 py-1 rounded-full text-sm">
                  LLM Token Throughput
                </span>
                <span className="bg-gray-700 px-3 py-1 rounded-full text-sm">
                  Cache Hit Ratio
                </span>
                <span className="bg-gray-700 px-3 py-1 rounded-full text-sm">
                  Error Rate
                </span>
                <span className="bg-gray-700 px-3 py-1 rounded-full text-sm">
                  Concurrent Requests
                </span>
                <span className="bg-gray-700 px-3 py-1 rounded-full text-sm">
                  Embedding P99
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

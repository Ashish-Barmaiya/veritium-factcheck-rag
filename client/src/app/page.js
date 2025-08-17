// app/page.js

"use client";
import { useState } from "react";
import Head from "next/head";

export default function Home() {
  const [claim, setClaim] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const verifyClaim = async () => {
    if (!claim.trim()) {
      setError("Please enter a claim to verify");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/factcheck", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ claim }),
      });

      const data = await response.json();

      let parsedLLM = {};
      try {
        parsedLLM = JSON.parse(data.llm_response);
      } catch {
        parsedLLM = {
          verdict: "Unverified",
          explanation: "Unable to parse LLM response",
          sources: [],
        };
      }

      setResult({
        claim: data.claim,
        verdict: parsedLLM.verdict,
        explanation: parsedLLM.explanation,
        sources: parsedLLM.sources,
        evidence: data.evidence,
      });
    } catch (err) {
      setError("Failed to verify claim. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const getVerdictColor = (verdict) => {
    switch (verdict?.toLowerCase()) {
      case "true":
        return "bg-green-500";
      case "false":
        return "bg-red-500";
      case "misleading":
        return "bg-yellow-500";
      default:
        return "bg-gray-400";
    }
  };

  return (
    <div className="flex flex-col min-h-screen relative overflow-hidden">
      <Head>
        <title>Veritium - AI Fact Checker</title>
        <meta name="description" content="Verify claims instantly with AI" />
        <link rel="icon" href="/veritium_icon.ico" />
      </Head>

      {/* Background */}

      <div className="absolute inset-0 bg-white">
        <svg
          className="absolute inset-0 w-full h-full opacity-60 text-gray-200"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="xMidYMid slice"
        >
          <rect width="100%" height="100%" fill="url(#veritium-bg)" />
        </svg>
      </div>

      {/* Main Content */}
      <main className="flex-grow relative z-10 flex flex-col">
        <div className="max-w-3xl mx-auto px-4 py-20 text-center flex-grow">
          <h1 className="text-4xl font-bold text-gray-900 mb-6">
            Check the Truth{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
              Instantly
            </span>
          </h1>
          <div className="flex items-center bg-white shadow-md rounded-full overflow-hidden border border-gray-200">
            <input
              type="text"
              placeholder='e.g. "COVID-19 vaccines contain microchips"'
              className="flex-1 px-5 py-3 text-gray-800 focus:outline-none"
              value={claim}
              onChange={(e) => setClaim(e.target.value)}
              disabled={isLoading}
            />
            <button
              onClick={verifyClaim}
              disabled={isLoading}
              className={`px-6 py-3 text-white font-medium transition ${
                isLoading
                  ? "bg-gray-400"
                  : "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              }`}
            >
              {isLoading ? "Checking..." : "Verify"}
            </button>
          </div>
          {error && <p className="text-red-500 mt-2">{error}</p>}
          <div className="max-w-3xl mx-auto px-4 mt-6 text-center flex-grow">
            <p className="text-lg">
              <span className="text-indigo-600 text-lg">
                AI fact-checking powered by RAG
              </span>{" "}
              <span className="text-gray-500">
                — truth in seconds, backed by trusted sources.
              </span>
            </p>
          </div>
        </div>

        {/* Result Section */}
        {result && (
          <div className="max-w-3xl mx-auto px-4 pb-20">
            <div className="bg-white shadow-lg rounded-lg p-6 border border-gray-100">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Verdict</h2>
                <span
                  className={`px-4 py-1 text-lg rounded-full text-white font-semibold ${getVerdictColor(
                    result.verdict
                  )}`}
                >
                  {result.verdict}
                </span>
              </div>
              {/* Extracted Evidence Title */}
              {result.evidence && (
                <p className="text-md font-semibold text-gray-800 mb-2">
                  {result.evidence
                    .split("(Source:")[0] // take only before "(Source:"
                    .replace(/^-/, "") // remove leading dash if present
                    .trim()}
                </p>
              )}
              <p className="text-gray-700 mb-4">{result.explanation}</p>
              <h3 className="font-semibold text-gray-900 mb-2">Sources</h3>
              <ul className="list-disc list-inside text-blue-600 space-y-1">
                {result.sources.length > 0 ? (
                  result.sources.map((src, i) => (
                    <li key={i}>
                      <a
                        href={src}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:underline"
                      >
                        {src}
                      </a>
                    </li>
                  ))
                ) : (
                  <li className="text-gray-500">No sources available</li>
                )}
              </ul>
              <details className="mt-6">
                <summary className="cursor-pointer text-sm text-gray-600">
                  Show Raw Evidence
                </summary>
                <pre className="bg-white text-gray-700 border border-gray-300 p-3 mt-2 rounded text-sm overflow-x-auto">
                  {result.evidence}
                </pre>
              </details>
            </div>
          </div>
        )}

        <div className="max-w-3xl mx-auto px-4 pb-20">
          <div className="bg-white shadow-lg rounded-lg p-6 border border-indigo-300">
            <div className="grid gap-2 justify-between mb-4">
              <h3 className="text-center text-gray-800 font-semibold text-2xl">
                About{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 ">
                  Veritium
                </span>
              </h3>
              <p className="text-gray-700 tracking-wide">
                Veritium is your{" "}
                <span className="text-pink-600">AI-powered fact-checking</span>{" "}
                companion. We analyze claims instantly using{" "}
                <span className="text-blue-600">
                  Retrieval-Augmented Generation (RAG)
                </span>{" "}
                technology — helping you fight misinformation and find the truth
                with just one click.
              </p>
            </div>
          </div>
        </div>
      </main>
      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4 text-center text-gray-500 text-sm relative z-10">
        © {new Date().getFullYear()} Veritium — Empowering Truth in the Digital
        Age
      </footer>
    </div>
  );
}

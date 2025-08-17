"use client";
import Head from "next/head";
import Link from "next/link";

export default function HowItWorks() {
  return (
    <div className="flex flex-col min-h-screen relative overflow-hidden">
      <Head>
        <title>How It Works - Veritium</title>
        <meta
          name="description"
          content="Learn how Veritium checks facts instantly"
        />
      </Head>

      {/* Background Pattern */}
      <div className="absolute inset-0 bg-white">
        <svg
          className="absolute inset-0 w-full h-full opacity-60 text-gray-200"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="xMidYMid slice"
        >
          <rect width="100%" height="100%" fill="url(#veritium-bg)" />
        </svg>
      </div>

      {/* Content */}
      <main className="flex-grow relative z-10 px-6 py-16 max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center text-gray-900 mb-4">
          How{" "}
          <span className="bg-gradient-to-r from-blue-600 to-purple-600 text-transparent bg-clip-text">
            Veritium
          </span>{" "}
          Works
        </h1>

        <p className="text-center mb-6 text-gray-400">
          {" "}
          To read technical details of Veritium{" "}
          <span className="text-blue-700">
            <Link href={"/how-it-works/technical"}>click here</Link>
          </span>
        </p>

        <div className="space-y-8">
          <div className="bg-white grid gap-5 shadow-lg rounded-lg py-6 px-10 border border-indigo-100">
            <div>
              <h2 className="text-xl font-semibold tracking-wide text-gray-800 mb-2">
                Collect Trusted Facts
              </h2>
              <p className="text-gray-600">
                We gather verified fact-checks from platforms like{" "}
                <span className="font-medium text-indigo-600">
                  Snopes, PolitiFact, BoomLive, and AltNews
                </span>
                . 👉{" "}
                <a href="/sources" className="text-blue-500 hover:underline">
                  See all sources
                </a>
              </p>
            </div>
            <div>
              <h2 className="text-xl tracking-wide font-semibold text-gray-800 mb-2">
                Understand Your Question
              </h2>
              <p className="text-gray-600">
                When you enter a claim, our AI understands the meaning — not
                just the words.
              </p>
            </div>
            <div>
              <h2 className="text-xl tracking-wide font-semibold text-gray-800 mb-2">
                Match with Reliable Facts
              </h2>
              <p className="text-gray-600">
                We instantly search our database to find the most relevant
                fact-check available.
              </p>
            </div>
            <div>
              <h2 className="text-xl tracking-wide font-semibold text-gray-800 mb-2">
                AI-Powered Summary
              </h2>
              <p className="text-gray-600">
                Finally, we create a short, clear summary so you can see the
                truth in seconds.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

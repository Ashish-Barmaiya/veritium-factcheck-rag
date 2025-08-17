// Navbar Component
"use client";

import { useState } from "react";
import Link from "next/link";
import Background from "@/components/Background";

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <nav className="bg-white/70 relative z-10">
      <div className="max-w-7xl mx-auto px-4 flex justify-between items-center h-14">
        <Link href={"/"}>
          <div className="flex items-center space-x-2">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 w-7 h-7 rounded-md flex items-center justify-center text-white font-bold">
              V
            </div>
            <span className="text-xl font-bold text-gray-800">Veritium</span>
          </div>
        </Link>

        {/* Desktop Links */}
        <div className="hidden md:flex space-x-6 text-gray-700 text-md">
          <a href="/how-it-works" className="hover:text-indigo-500">
            How it works
          </a>
          <a href="#" className="hover:text-indigo-500">
            Sources
          </a>
          <a href="#" className="hover:text-indigo-500">
            About
          </a>
        </div>

        {/* Mobile Menu */}
        <button
          className="md:hidden text-gray-700 focus:outline-none"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          ☰
        </button>
      </div>

      {menuOpen && (
        <div className="md:hidden px-4 py-4 pb-3 space-y-2 bg-white border-t text-center">
          <a href="#" className="block text-gray-600 hover:text-indigo-500">
            How it works
          </a>
          <a href="#" className="block text-gray-600 hover:text-indigo-500">
            Sources
          </a>
          <a href="#" className="block text-gray-600 hover:text-indigo-500">
            About
          </a>
        </div>
      )}
    </nav>
  );
}

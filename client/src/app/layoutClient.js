"use client";
import Navbar from "@/components/Navbar";
import Background from "@/components/Background";
import { usePathname } from "next/navigation";

export default function ClientLayout() {
  const pathname = usePathname();

  if (!pathname.startsWith("/technical")) {
    <>
      <Background />
      <Navbar />
    </>;
  }
}

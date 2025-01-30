"use client";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { useTheme } from "next-themes";

interface ConcertItem {
    id: number;
    title: string;
    date: string;
    artist: string;
    location: string;
}

function ConcertList() {
    const [concerts, setConcerts] = useState<ConcertItem[]>([]);

    useEffect(() => {
        async function fetchConcerts() {
            const response = await fetch(
                "http://127.0.0.1:8000/api/v2/pages/?type=api.ConcertIndexPage&fields=_,id,title,artist,date,location",
                {
                    headers: { Accept: "application/json" },
                }
            );
            const data = await response.json();
            console.log(data.items);
            setConcerts(data.items);
        }
        fetchConcerts().catch((error) =>
            console.error("Failed to fetch concerts:", error)
        );
    }, []);

    return (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 px-4 py-8">
            {concerts.map((concert) => (
                <ConcertCard key={concert.id} concert={concert} />
            ))}
        </div>
    );
}

function ConcertCard({ concert }: { concert: ConcertItem }) {
    return (
        <Card className="w-full max-w-sm transition-transform duration-300 ease-in-out hover:scale-105 hover:shadow-lg">
            <CardHeader>
                <CardTitle className="text-xl font-bold">
                    {concert.title}
                </CardTitle>
                <CardDescription className="text-sm text-gray-500">
                    {concert.artist}
                </CardDescription>
            </CardHeader>
            <CardContent>
                <p className="text-sm text-muted-foreground">
                    <strong>Date:</strong> {concert.date}
                </p>
                <p className="text-sm text-muted-foreground">
                    <strong>Location:</strong> {concert.location}
                </p>
            </CardContent>
            <CardFooter className="flex justify-end space-x-2">
                <Button variant="outline">Details</Button>
                <Button>Buy Tickets</Button>
            </CardFooter>
        </Card>
    );
}

export default function Home() {
    const { setTheme } = useTheme();
    setTheme("light");
    return (
        <div className="flex flex-col items-center justify-center min-h-screen px-4 py-8">
            <div className="mb-6">
                <h1 className="text-3xl font-bold leading-tight tracking-tighter md:text-4xl lg:leading-[1.1]">
                    Concerts
                </h1>
            </div>
            <div className="w-full max-w-6xl border-4 border-gray-300 rounded-lg bg-white p-6">
                <ConcertList />
            </div>
        </div>
    );
}

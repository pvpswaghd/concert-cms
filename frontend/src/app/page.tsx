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

interface ConcertItem {
    id: number;
    title: string;
    date: string;
    artist: string;
}

function ConcertList() {
    const [concerts, setConcerts] = useState<ConcertItem[]>([]);

    useEffect(() => {
        async function fetchConcerts() {
            const response = await fetch(
                "http://127.0.0.1:8000/api/v2/pages/?type=api.ConcertIndexPage&fields=_,id,title,artist,date",
                {
                    headers: { Accept: "application/json" },
                }
            );
            const data = await response.json();
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
        <Card className="w-full max-w-sm">
            <CardHeader>
                <CardTitle>{concert.title}</CardTitle>
                <CardDescription>{concert.artist}</CardDescription>
            </CardHeader>
            <CardContent>
                <p className="text-sm text-muted-foreground">
                    <strong>Date:</strong> {concert.date}
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
    return <ConcertList />;
}

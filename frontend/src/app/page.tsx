"use client";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { useTheme } from "next-themes";
import { useToast } from "@/hooks/use-toast";

interface ConcertItem {
    id: number;
    title: string;
    date: string;
    artist: string;
    venue: string;
    slug: string;
    sold_out: boolean;
    description: string;
    start_time: string;
    end_time: string;
    image_url: string | null;
}

function ConcertList() {
    const [concerts, setConcerts] = useState<ConcertItem[]>([]);
    const { toast } = useToast();

    useEffect(() => {
        async function fetchConcerts() {
            try {
                const response = await fetch(
                    "http://localhost:8000/api/concerts/", // New endpoint from your API
                    { headers: { Accept: "application/json" } }
                );
                const data = await response.json();
                setConcerts(data);
            } catch (error) {
                toast({
                    title: "Error",
                    description: "Failed to load concerts",
                    variant: "destructive",
                });
            }
        }
        fetchConcerts();
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
    const { toast } = useToast();
    const router = useRouter();
    const handleCardClick = () => {
        navigator.clipboard.writeText(concert.slug);
        router.push(`/${concert.slug}`);
        toast({
            title: "Concert Slug",
            description: `${concert.slug} copied to clipboard!`,
        });
    };

    return (
        <Card
            className={`w-full max-w-sm transition-transform duration-300 ease-in-out ${
                concert.sold_out
                    ? "opacity-50 cursor-not-allowed"
                    : "hover:scale-105 hover:shadow-lg cursor-pointer"
            }`}
            onClick={handleCardClick}
        >
            <CardHeader>
                <CardTitle className="text-xl font-bold">
                    {concert.title}
                </CardTitle>
                <CardDescription className="text-sm text-gray-500">
                    {concert.artist}
                </CardDescription>
            </CardHeader>
            <CardContent>
                <p className="text-md italic">{concert.description}</p>
                <div className="mt-4 space-y-1">
                    <p className="text-sm text-muted-foreground">
                        <strong>Date:</strong>{" "}
                        {new Date(concert.date).toLocaleDateString()}
                    </p>
                    <p className="text-sm text-muted-foreground">
                        <strong>Time:</strong> {concert.start_time} -{" "}
                        {concert.end_time || "N/A"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                        <strong>Venue:</strong> {concert.venue}
                    </p>
                </div>
            </CardContent>
            <CardFooter className="flex justify-end space-x-2">
                <Button variant="outline">Details</Button>
                <Button disabled={concert.sold_out}>
                    {concert.sold_out ? "Sold Out" : "Buy Tickets"}
                </Button>
            </CardFooter>
        </Card>
    );
}

export default function Home() {
    const { setTheme } = useTheme();
    setTheme("light");

    return (
        <div className="flex flex-col items-center justify-center min-h-screen px-4 py-8">
            <div className="mb-6 text-center">
                <h1 className="text-3xl font-bold leading-tight tracking-tighter md:text-4xl lg:leading-[1.1]">
                    Upcoming Concerts
                </h1>
                <p className="text-muted-foreground mt-2">
                    Click any card to copy concert ID (slug)
                </p>
            </div>
            <div className="w-full max-w-6xl border-4 border-gray-300 rounded-lg bg-white p-6">
                <ConcertList />
            </div>
        </div>
    );
}

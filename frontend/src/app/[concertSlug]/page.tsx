// app/[concertSlug]/page.tsx
import { notFound } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import Image from "next/image";

interface Concert {
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
    genre: string;
    image_url: string;
    ticket_types: {
        type: string;
        price: number;
        remaining: number;
        is_sold_out: boolean;
        seat_zone?: string;
        capacity?: number;
    }[];
}

async function getConcert(slug: string): Promise<Concert> {
    const res = await fetch(`http://localhost:8000/api/concerts/${slug}/`);
    console.log(res);
    if (!res.ok) throw new Error("Failed to fetch concert");
    return res.json();
}

export default async function ConcertDetailPage({
    params,
}: {
    params: { concertSlug: string };
}) {
    let concert: Concert | null = null;

    try {
        concert = await getConcert(params.concertSlug);
        console.log(concert);
    } catch (error) {
        console.log(error);
        notFound();
    }
    console.log(concert);

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white py-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Concert Header */}
                <div className="mb-12 grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="relative h-96 rounded-2xl overflow-hidden shadow-xl">
                        {concert.image_url ? (
                            <Image
                                src={concert.image_url}
                                alt={concert.title}
                                fill
                                className="object-cover"
                            />
                        ) : (
                            <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500" />
                        )}
                        <div className="absolute inset-0 bg-black/30 flex items-end p-6">
                            <Badge
                                variant="secondary"
                                className="text-sm py-1 px-3"
                            >
                                {concert.genre}
                            </Badge>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h1 className="text-4xl font-bold tracking-tight text-gray-900">
                            {concert.title}
                        </h1>
                        <div className="flex items-center space-x-4 text-lg text-gray-600">
                            <p>
                                {new Date(concert.date).toLocaleDateString(
                                    "en-US",
                                    {
                                        year: "numeric",
                                        month: "long",
                                        day: "numeric",
                                    }
                                )}
                            </p>
                            <span>•</span>
                            <p>
                                {concert.start_time} - {concert.end_time}
                            </p>
                        </div>
                        <p className="text-xl font-semibold text-gray-900">
                            {concert.artist} @ {concert.venue}
                        </p>
                        <Badge
                            variant={
                                concert.sold_out ? "destructive" : "default"
                            }
                            className="text-sm"
                        >
                            {concert.sold_out
                                ? "Sold Out"
                                : "Tickets Available"}
                        </Badge>
                        <p className="text-gray-600 mt-4 leading-relaxed">
                            {concert.description}
                        </p>
                    </div>
                </div>

                {/* Ticket Types Table */}
                <Card className="shadow-lg">
                    <CardHeader>
                        <CardTitle className="text-2xl">
                            Ticket Options
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Type</TableHead>
                                    <TableHead>Price</TableHead>
                                    <TableHead>Availability</TableHead>
                                    <TableHead className="text-right">
                                        Action
                                    </TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {concert.ticket_types.map((ticket) => (
                                    <TableRow
                                        key={`${ticket.type}-${
                                            ticket.seat_zone || ""
                                        }`}
                                    >
                                        <TableCell className="font-medium">
                                            <div className="flex flex-col">
                                                <span>{ticket.type}</span>
                                                {ticket.seat_zone && (
                                                    <div className="text-sm text-gray-500 mt-1">
                                                        <p>
                                                            Zone:{" "}
                                                            {
                                                                ticket.seat_zone
                                                                    .name
                                                            }
                                                        </p>
                                                        <p>
                                                            Total Seats:{" "}
                                                            {
                                                                ticket.seat_zone
                                                                    .total_seats
                                                            }
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            ${ticket.price.toFixed(2)}
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <span
                                                    className={
                                                        ticket.remaining < 10
                                                            ? "text-red-600"
                                                            : "text-green-600"
                                                    }
                                                >
                                                    {ticket.remaining} left
                                                </span>
                                                {ticket.is_sold_out && (
                                                    <Badge
                                                        variant="destructive"
                                                        className="px-2 py-1 text-xs"
                                                    >
                                                        Sold Out
                                                    </Badge>
                                                )}
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button
                                                variant={
                                                    ticket.is_sold_out
                                                        ? "ghost"
                                                        : "default"
                                                }
                                                disabled={ticket.is_sold_out}
                                            >
                                                {ticket.is_sold_out
                                                    ? "Unavailable"
                                                    : "Buy Now"}
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>

                {/* Venue Map Section */}
                <div className="mt-12">
                    <Card className="shadow-lg">
                        <CardHeader>
                            <CardTitle className="text-2xl">
                                Venue Map
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
                                <span className="text-gray-500">
                                    Venue map coming soon
                                </span>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}

export const revalidate = 0;

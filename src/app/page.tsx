import { redirect } from "next/navigation";

export default function EmptyPage() {
    // default switched to channel-ind
    redirect("/channel-ind");
}

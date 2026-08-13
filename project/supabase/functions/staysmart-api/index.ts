import { createClient } from "jsr:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders },
  });
}

interface PricingRule {
  room_type: string;
  weekend_multiplier: number;
  high_occupancy_multiplier: number;
  last_minute_multiplier: number;
}

function calculatePrice(
  basePrice: number,
  checkIn: string,
  rule: PricingRule,
  occupancy: number,
  totalRooms: number,
): number {
  let price = basePrice;
  const checkInDate = new Date(checkIn + "T00:00:00");
  const dayOfWeek = checkInDate.getDay();

  if (dayOfWeek === 5 || dayOfWeek === 6) {
    price *= Number(rule.weekend_multiplier);
  }

  const occupancyRate = totalRooms > 0 ? occupancy / totalRooms : 0;
  if (occupancyRate > 0.8) {
    price *= Number(rule.high_occupancy_multiplier);
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil(
    (checkInDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24),
  );
  if (diffDays <= 3 && diffDays >= 0) {
    price *= Number(rule.last_minute_multiplier);
  }

  return Math.round(price);
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  );

  const url = new URL(req.url);
  const path = url.pathname;
  const method = req.method;

  try {
    // ── POST /login/ ──────────────────────────────
    if (/\/login\/?$/.test(path) && method === "POST") {
      const { email, password } = await req.json();
      const { data, error } = await supabase
        .from("app_users")
        .select("email, role, name")
        .eq("email", (email || "").toLowerCase())
        .eq("password", password)
        .maybeSingle();

      if (error || !data) {
        return json(
          { status: "error", message: "Invalid email or password." },
          401,
        );
      }
      return json({ status: "success", role: data.role, email: data.email });
    }

    // ── GET /rooms/ ───────────────────────────────
    if (/\/rooms\/?$/.test(path) && method === "GET") {
      const checkIn = url.searchParams.get("checkIn");

      const { data: rooms, error: roomsErr } = await supabase
        .from("rooms")
        .select("*")
        .order("id");
      if (roomsErr) throw roomsErr;

      const { data: rules } = await supabase
        .from("pricing_rules")
        .select("*");

      // Count bookings overlapping the check-in date per room type
      const occupancyByType: Record<string, number> = {};
      if (checkIn) {
        const { data: overlapping } = await supabase
          .from("bookings")
          .select("room")
          .neq("status", "Cancelled")
          .lte("check_in", checkIn)
          .gt("check_out", checkIn);

        overlapping?.forEach((b) => {
          occupancyByType[b.room] = (occupancyByType[b.room] || 0) + 1;
        });
      }

      const result = (rooms || []).map((r) => {
        const rule = (rules || []).find(
          (rl: PricingRule) => rl.room_type === r.room_type,
        );
        const occupancy = occupancyByType[r.room_type] || 0;
        let calculatedPrice = r.base_price;

        if (checkIn && rule) {
          calculatedPrice = calculatePrice(
            r.base_price,
            checkIn,
            rule,
            occupancy,
            r.total_rooms,
          );
        }

        return {
          id: r.id,
          title: r.title,
          room_type: r.room_type,
          room_number: r.room_number,
          base_price: r.base_price,
          calculated_price: calculatedPrice,
          capacity: r.capacity,
          total_rooms: r.total_rooms,
          amenities: r.amenities,
          image_key: r.image_key,
        };
      });

      return json({ status: "success", rooms: result });
    }

    // ── POST /bookings/ ───────────────────────────
    if (/\/bookings\/?$/.test(path) && method === "POST") {
      const body = await req.json();

      const { data: seqData } = await supabase.rpc("next_booking_id");
      const bookingId = seqData || `BK-${Date.now().toString().slice(-6)}`;

      const { data, error } = await supabase
        .from("bookings")
        .insert({
          id: bookingId,
          guest_name: body.guestName,
          guest_email: body.guestEmail,
          room: body.room,
          room_id: body.roomId || null,
          check_in: body.checkIn,
          check_out: body.checkOut,
          guests: body.guests || 1,
          price_paid: body.pricePaid,
          status: "Confirmed",
        })
        .select()
        .single();

      if (error) throw error;
      return json({ status: "success", booking: { id: data.id } });
    }

    // ── GET /bookings/ ────────────────────────────
    if (/\/bookings\/?$/.test(path) && method === "GET") {
      const { data, error } = await supabase
        .from("bookings")
        .select("*")
        .order("created_at", { ascending: false });
      if (error) throw error;

      const bookings = (data || []).map((b) => ({
        id: b.id,
        guestName: b.guest_name,
        guestEmail: b.guest_email,
        room: b.room,
        roomId: b.room_id,
        checkIn: b.check_in,
        checkOut: b.check_out,
        guests: b.guests,
        pricePaid: b.price_paid,
        status: b.status,
      }));

      return json({ status: "success", bookings });
    }

    // ── POST /bookings/:id/status/ ────────────────
    const statusMatch = path.match(/\/bookings\/([^/]+)\/status\/?$/);
    if (statusMatch && method === "POST") {
      const id = decodeURIComponent(statusMatch[1]);
      const { status } = await req.json();

      const { error } = await supabase
        .from("bookings")
        .update({ status })
        .eq("id", id);
      if (error) throw error;

      return json({ status: "success" });
    }

    // ── GET /admin/stats/ ─────────────────────────
    if (/\/admin\/stats\/?$/.test(path) && method === "GET") {
      const { data: bookings } = await supabase
        .from("bookings")
        .select("*");
      const { data: roomRows } = await supabase
        .from("rooms")
        .select("total_rooms");
      const totalRooms = (roomRows || []).reduce(
        (sum: number, r: { total_rooms: number }) => sum + r.total_rooms,
        0,
      );

      const today = new Date().toISOString().split("T")[0];
      let totalRevenue = 0;
      let checkedInCount = 0;
      let checkInsToday = 0;
      let checkOutsToday = 0;

      (bookings || []).forEach((b) => {
        if (b.status !== "Cancelled") {
          totalRevenue += Number(b.price_paid || 0);
        }
        if (b.status === "Checked-In") checkedInCount++;
        if (b.check_in === today) checkInsToday++;
        if (b.check_out === today) checkOutsToday++;
      });

      const occupancyPercentage = totalRooms > 0
        ? Math.round((checkedInCount / totalRooms) * 100)
        : 0;

      return json({
        status: "success",
        kpis: {
          totalRevenue,
          totalBookings: (bookings || []).length,
          occupancyPercentage,
          checkedInCount,
          totalRooms,
          checkInsToday,
          checkOutsToday,
        },
      });
    }

    // ── GET /pricing-rules/ ───────────────────────
    if (/\/pricing-rules\/?$/.test(path) && method === "GET") {
      const { data, error } = await supabase
        .from("pricing_rules")
        .select("*")
        .order("id");
      if (error) throw error;
      return json({ status: "success", rules: data });
    }

    // ── POST /pricing-rules/ ──────────────────────
    if (/\/pricing-rules\/?$/.test(path) && method === "POST") {
      const body = await req.json();
      const { error } = await supabase
        .from("pricing_rules")
        .update({
          weekend_multiplier: body.weekendMultiplier,
          high_occupancy_multiplier: body.highOccupancyMultiplier,
          updated_at: new Date().toISOString(),
        })
        .eq("room_type", body.roomType);
      if (error) throw error;
      return json({ status: "success" });
    }

    return json({ status: "error", message: "Not found" }, 404);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Internal server error";
    return json({ status: "error", message }, 500);
  }
});

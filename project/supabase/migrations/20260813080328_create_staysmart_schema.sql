-- StaySmart hotel booking platform schema

-- App users (simple auth for the demo frontend)
CREATE TABLE app_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text UNIQUE NOT NULL,
  password text NOT NULL,
  role text NOT NULL CHECK (role IN ('admin', 'guest')),
  name text,
  created_at timestamptz DEFAULT now()
);

-- Room types catalog
CREATE TABLE rooms (
  id serial PRIMARY KEY,
  title text NOT NULL,
  room_type text NOT NULL,
  room_number text NOT NULL,
  base_price integer NOT NULL,
  capacity integer NOT NULL,
  total_rooms integer NOT NULL,
  amenities text[] NOT NULL DEFAULT '{}',
  image_key text NOT NULL
);

-- Bookings
CREATE TABLE bookings (
  id text PRIMARY KEY,
  guest_name text NOT NULL,
  guest_email text NOT NULL,
  room text NOT NULL,
  room_id text,
  check_in date NOT NULL,
  check_out date NOT NULL,
  guests integer NOT NULL DEFAULT 1,
  price_paid integer NOT NULL,
  status text NOT NULL DEFAULT 'Confirmed'
    CHECK (status IN ('Confirmed', 'Checked-In', 'Checked-Out', 'Cancelled')),
  created_at timestamptz DEFAULT now()
);

-- Dynamic pricing rules per room type
CREATE TABLE pricing_rules (
  id serial PRIMARY KEY,
  room_type text UNIQUE NOT NULL,
  weekend_multiplier numeric NOT NULL DEFAULT 1.15,
  high_occupancy_multiplier numeric NOT NULL DEFAULT 1.25,
  last_minute_multiplier numeric NOT NULL DEFAULT 1.10,
  updated_at timestamptz DEFAULT now()
);

-- Sequence for booking IDs (BK-1001, BK-1002, ...)
CREATE SEQUENCE booking_id_seq START 1001;

-- Function to generate next booking ID
CREATE OR REPLACE FUNCTION next_booking_id()
RETURNS text
LANGUAGE plpgsql
AS $$
DECLARE
  next_val integer;
BEGIN
  SELECT nextval('booking_id_seq') INTO next_val;
  RETURN 'BK-' || next_val;
END;
$$;

-- Enable RLS on all tables (deny direct browser access; edge function uses service role key)
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE pricing_rules ENABLE ROW LEVEL SECURITY;

-- Grant execute on the booking ID function
GRANT EXECUTE ON FUNCTION next_booking_id() TO anon, authenticated;

-- ============ SEED DATA ============

-- Users
INSERT INTO app_users (email, password, role, name) VALUES
  ('admin@staysmart.com', 'admin123', 'admin', 'Hotel Manager'),
  ('guest@example.com', 'guest123', 'guest', 'Demo Guest');

-- Rooms
INSERT INTO rooms (title, room_type, room_number, base_price, capacity, total_rooms, amenities, image_key) VALUES
  ('Deluxe Room', 'Deluxe Room', '101', 2499, 2, 10,
   ARRAY['Wi-Fi', 'AC', 'Smart TV', 'King Bed'], 'deluxe'),
  ('Premium Suite', 'Premium Suite', '201', 4499, 3, 6,
   ARRAY['Wi-Fi', 'AC', 'Breakfast', 'King Bed'], 'premium'),
  ('Family Suite', 'Family Suite', '301', 6999, 5, 3,
   ARRAY['Wi-Fi', 'AC', 'Living Room', 'Breakfast'], 'family');

-- Pricing rules
INSERT INTO pricing_rules (room_type, weekend_multiplier, high_occupancy_multiplier, last_minute_multiplier) VALUES
  ('Deluxe Room', 1.15, 1.25, 1.10),
  ('Premium Suite', 1.15, 1.30, 1.10),
  ('Family Suite', 1.20, 1.35, 1.10);

-- Sample bookings
INSERT INTO bookings (id, guest_name, guest_email, room, room_id, check_in, check_out, guests, price_paid, status) VALUES
  ('BK-1001', 'Priya Sharma', 'priya.s@example.com', 'Deluxe Room', '101', '2026-08-12', '2026-08-15', 2, 7497, 'Checked-In'),
  ('BK-1002', 'Vikram Malhotra', 'vikram.m@example.com', 'Premium Suite', '201', '2026-08-13', '2026-08-16', 2, 13497, 'Confirmed'),
  ('BK-1003', 'Ananya Roy', 'ananya.roy@example.com', 'Family Suite', '301', '2026-08-10', '2026-08-12', 4, 13998, 'Checked-Out');

-- Sync the sequence past seed data
SELECT setval('booking_id_seq', 1003);

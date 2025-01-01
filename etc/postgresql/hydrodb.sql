--
-- PostgreSQL database dump
--

-- Dumped from database version 11.22 (Debian 11.22-0+deb10u1)
-- Dumped by pg_dump version 13.18 (Debian 13.18-0+deb11u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE hydrodb;
--
-- Name: hydrodb; Type: DATABASE; Schema: -; Owner: hydrodbuser
--

CREATE DATABASE hydrodb WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE = 'en_US.UTF-8';


ALTER DATABASE hydrodb OWNER TO hydrodbuser;

\connect hydrodb

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

--
-- Name: data_feeds; Type: TABLE; Schema: public; Owner: hydrodbuser
--

CREATE TABLE public.data_feeds (
    feed_id text,
    mqtt_broker text,
    mqtt_password text,
    mqtt_port integer,
    mqtt_user text,
    is_ttn_feed boolean,
    mqtt_topic text
);


ALTER TABLE public.data_feeds OWNER TO hydrodbuser;

--
-- Name: hydro_alerts; Type: TABLE; Schema: public; Owner: hydrodbuser
--

CREATE TABLE public.hydro_alerts (
    received_at timestamp with time zone,
    message_number text,
    message_text text
);


ALTER TABLE public.hydro_alerts OWNER TO hydrodbuser;

--
-- Name: hydro_data; Type: TABLE; Schema: public; Owner: hydrodbuser
--

CREATE TABLE public.hydro_data (
    received_at timestamp with time zone NOT NULL,
    downstream double precision,
    upstream double precision,
    forebay_1 double precision,
    forebay_2 double precision,
    gen1_power_kw double precision,
    gen1_drive_rpm double precision,
    gen1_screw_rpm double precision,
    gen1_flow_ls double precision,
    gen1_inverter_amp double precision,
    gen1_total_flow_m3 double precision,
    gen1_operating_hours double precision,
    gen1_gearbox_temp double precision,
    gen1_energy_mwh double precision,
    gen1_torque double precision,
    gen2_power_kw double precision,
    gen2_drive_rpm double precision,
    gen2_screw_rpm double precision,
    gen2_flow_ls double precision,
    gen2_inverter_amp double precision,
    gen2_total_flow_m3 double precision,
    gen2_operating_hours double precision,
    gen2_gearbox_temp double precision,
    gen2_energy_mwh double precision,
    gen2_torque double precision,
    room_temp double precision,
    control_panel_temp double precision
);


ALTER TABLE public.hydro_data OWNER TO hydrodbuser;

--
-- Name: hydro_meter; Type: TABLE; Schema: public; Owner: hydrodbuser
--

CREATE TABLE public.hydro_meter (
    m1_datetime timestamp without time zone NOT NULL,
    m1_import double precision,
    m1_export double precision,
    meter_serial_no text NOT NULL
);


ALTER TABLE public.hydro_meter OWNER TO hydrodbuser;

--
-- Name: hydro_sluice; Type: TABLE; Schema: public; Owner: hydrodbuser
--

CREATE TABLE public.hydro_sluice (
    received_at timestamp without time zone NOT NULL,
    sensor text NOT NULL,
    gate_raised_mm integer,
    accuracy_mm integer
);


ALTER TABLE public.hydro_sluice OWNER TO hydrodbuser;

--
-- Name: sensor_data; Type: TABLE; Schema: public; Owner: hydrodbuser
--

CREATE TABLE public.sensor_data (
    sensor_ref integer,
    received_at timestamp with time zone,
    ttn_payload_fields text,
    light_level integer,
    people_count integer,
    sound_level integer,
    sound_category text,
    counter integer,
    gateways text,
    rssi double precision,
    snr double precision,
    temperature double precision,
    humidity double precision,
    door_status text,
    battery integer,
    smoke_status text
);


ALTER TABLE public.sensor_data OWNER TO hydrodbuser;

--
-- Name: sensors; Type: TABLE; Schema: public; Owner: hydrodbuser
--

CREATE TABLE public.sensors (
    ttn_device_id text,
    ttn_application_id text,
    sensor_ref integer NOT NULL,
    longitude double precision,
    latitude double precision
);


ALTER TABLE public.sensors OWNER TO hydrodbuser;

--
-- Name: sensors_sensor_ref_seq; Type: SEQUENCE; Schema: public; Owner: hydrodbuser
--

CREATE SEQUENCE public.sensors_sensor_ref_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sensors_sensor_ref_seq OWNER TO hydrodbuser;

--
-- Name: sensors_sensor_ref_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hydrodbuser
--

ALTER SEQUENCE public.sensors_sensor_ref_seq OWNED BY public.sensors.sensor_ref;


--
-- Name: set_level; Type: TABLE; Schema: public; Owner: hydrodbuser
--

CREATE TABLE public.set_level (
    level numeric NOT NULL,
    user_id text,
    changed_at timestamp without time zone NOT NULL
);


ALTER TABLE public.set_level OWNER TO hydrodbuser;

--
-- Name: th_alarms; Type: TABLE; Schema: public; Owner: hydrodbuser
--

CREATE TABLE public.th_alarms (
    th_alarms_active boolean,
    changed_at timestamp without time zone NOT NULL,
    user_id text
);


ALTER TABLE public.th_alarms OWNER TO hydrodbuser;

--
-- Name: sensors sensor_ref; Type: DEFAULT; Schema: public; Owner: hydrodbuser
--

ALTER TABLE ONLY public.sensors ALTER COLUMN sensor_ref SET DEFAULT nextval('public.sensors_sensor_ref_seq'::regclass);


--
-- Name: hydro_data hydro_data_pkey; Type: CONSTRAINT; Schema: public; Owner: hydrodbuser
--

ALTER TABLE ONLY public.hydro_data
    ADD CONSTRAINT hydro_data_pkey PRIMARY KEY (received_at);


--
-- Name: hydro_meter hydro_meter_pk; Type: CONSTRAINT; Schema: public; Owner: hydrodbuser
--

ALTER TABLE ONLY public.hydro_meter
    ADD CONSTRAINT hydro_meter_pk PRIMARY KEY (m1_datetime, meter_serial_no);


--
-- Name: hydro_sluice hydro_sluice_pkey; Type: CONSTRAINT; Schema: public; Owner: hydrodbuser
--

ALTER TABLE ONLY public.hydro_sluice
    ADD CONSTRAINT hydro_sluice_pkey PRIMARY KEY (received_at, sensor);


--
-- Name: set_level set_level_pkey; Type: CONSTRAINT; Schema: public; Owner: hydrodbuser
--

ALTER TABLE ONLY public.set_level
    ADD CONSTRAINT set_level_pkey PRIMARY KEY (changed_at);


--
-- Name: th_alarms th_alarms_pkey; Type: CONSTRAINT; Schema: public; Owner: hydrodbuser
--

ALTER TABLE ONLY public.th_alarms
    ADD CONSTRAINT th_alarms_pkey PRIMARY KEY (changed_at);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

GRANT ALL ON SCHEMA public TO hydrodbuser;


--
-- PostgreSQL database dump complete
--


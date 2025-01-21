CREATE TABLE public.eadata (
    entrytime timestamptz NOT NULL, 
    flow double precision);

ALTER TABLE public.eadata OWNER TO hydrodbuser;

ALTER TABLE ONLY public.eadata ADD CONSTRAINT eadata_pkey PRIMARY KEY (entrytime);

-- Dummy entry for the start of recorded data

INSERT INTO public.eadata(2025-01-01T00:00:00ZS, 0.0);

CREATE MATERIALIZED VIEW h_eadata
AS SELECT
    date_trunc('hour', eadata.entrytime) AS entrytime,
    ROUND(avg(eadata.flow)::numeric,3) AS flow
FROM public.eadata
GROUP BY h_eadata.entrytime;

CREATE MATERIALIZED VIEW d_eadata
AS SELECT
    date_trunc('day', eadata.entrytime) AS entrytime,
    ROUND(avg(eadata.flow)::numeric,3) AS flow
FROM public.eadata
GROUP BY d_eadata.entrytime;

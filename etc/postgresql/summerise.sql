
CREATE MATERIALIZED VIEW d_hydro_data
AS SELECT 
    date_trunc('day', hydro_data.received_at) AS received_at,
    ROUND(avg(hydro_data.downstream)::numeric,3) AS downstream,
    ROUND(avg(hydro_data.upstream)::numeric,3) AS upstream,
    ROUND(avg(hydro_data.forebay_1)::numeric,3) AS forebay_1,
    ROUND(avg(hydro_data.forebay_2)::numeric,3) AS forebay_2,
    ROUND(avg(hydro_data.gen1_power_kw)::numeric,3) AS gen1_power_kw,
    ROUND(avg(hydro_data.gen1_drive_rpm)::numeric,0) AS gen1_drive_rpm,
    ROUND(avg(hydro_data.gen1_screw_rpm)::numeric,0) AS gen1_screw_rpm,
    ROUND(avg(hydro_data.gen1_flow_ls)::numeric,0) AS gen1_flow_ls,
    ROUND(avg(hydro_data.gen1_inverter_amp)::numeric,0) AS gen1_inverter_amp,
    ROUND(avg(hydro_data.gen1_total_flow_m3)::numeric,0) AS gen1_total_flow_m3,
    max(hydro_data.gen1_operating_hours) AS gen1_operating_hours,
    ROUND(avg(hydro_data.gen1_gearbox_temp)::numeric,0) AS gen1_gearbox_temp,
    ROUND(max(hydro_data.gen1_energy_mwh)::numeric,3) AS gen1_energy_mwh,
    ROUND(avg(hydro_data.gen1_torque)::numeric,0) AS gen1_torque,
    ROUND(avg(hydro_data.gen2_power_kw)::numeric,3) AS gen2_power_kw,
    ROUND(avg(hydro_data.gen2_drive_rpm)::numeric,0) AS gen2_drive_rpm,
    ROUND(avg(hydro_data.gen2_screw_rpm)::numeric,0) AS gen2_screw_rpm,
    ROUND(avg(hydro_data.gen2_flow_ls)::numeric,0) AS gen2_flow_ls,
    ROUND(avg(hydro_data.gen2_inverter_amp)::numeric,0) AS gen2_inverter_amp,
    ROUND(avg(hydro_data.gen2_total_flow_m3)::numeric,0) AS gen2_total_flow_m3,
    max(hydro_data.gen2_operating_hours) AS gen2_operating_hours,
    ROUND(avg(hydro_data.gen2_gearbox_temp)::numeric,0) AS gen2_gearbox_temp,
    ROUND(max(hydro_data.gen2_energy_mwh)::numeric,3) AS gen2_energy_mwh,
    ROUND(avg(hydro_data.gen2_torque)::numeric,0) AS gen2_torque,
    ROUND(avg(hydro_data.room_temp)::numeric,2) AS room_temp,
    ROUND(avg(hydro_data.control_panel_temp)::numeric,2) AS control_panel_temp
FROM public.hydro_data
GROUP BY date_trunc('day',hydro_data.received_at);

CREATE UNIQUE INDEX ON d_hydro_data (received_at);

REFRESH MATERIALIZED VIEW d_hydro_data;

SELECT * FROM d_hydro_data ORDER BY received_at DESC LIMIT 5;


CREATE MATERIALIZED VIEW h_hydro_data
AS SELECT 
    date_trunc('hour', hydro_data.received_at) AS received_at,
    ROUND(avg(hydro_data.downstream)::numeric,3) AS downstream,
    ROUND(avg(hydro_data.upstream)::numeric,3) AS upstream,
    ROUND(avg(hydro_data.forebay_1)::numeric,3) AS forebay_1,
    ROUND(avg(hydro_data.forebay_2)::numeric,3) AS forebay_2,
    ROUND(avg(hydro_data.gen1_power_kw)::numeric,3) AS gen1_power_kw,
    ROUND(avg(hydro_data.gen1_drive_rpm)::numeric,0) AS gen1_drive_rpm,
    ROUND(avg(hydro_data.gen1_screw_rpm)::numeric,0) AS gen1_screw_rpm,
    ROUND(avg(hydro_data.gen1_flow_ls)::numeric,0) AS gen1_flow_ls,
    ROUND(avg(hydro_data.gen1_inverter_amp)::numeric,0) AS gen1_inverter_amp,
    ROUND(avg(hydro_data.gen1_total_flow_m3)::numeric,0) AS gen1_total_flow_m3,
    max(hydro_data.gen1_operating_hours) AS gen1_operating_hours,
    ROUND(avg(hydro_data.gen1_gearbox_temp)::numeric,0) AS gen1_gearbox_temp,
    ROUND(max(hydro_data.gen1_energy_mwh)::numeric,3) AS gen1_energy_mwh,
    ROUND(avg(hydro_data.gen1_torque)::numeric,0) AS gen1_torque,
    ROUND(avg(hydro_data.gen2_power_kw)::numeric,3) AS gen2_power_kw,
    ROUND(avg(hydro_data.gen2_drive_rpm)::numeric,0) AS gen2_drive_rpm,
    ROUND(avg(hydro_data.gen2_screw_rpm)::numeric,0) AS gen2_screw_rpm,
    ROUND(avg(hydro_data.gen2_flow_ls)::numeric,0) AS gen2_flow_ls,
    ROUND(avg(hydro_data.gen2_inverter_amp)::numeric,0) AS gen2_inverter_amp,
    ROUND(avg(hydro_data.gen2_total_flow_m3)::numeric,0) AS gen2_total_flow_m3,
    max(hydro_data.gen2_operating_hours) AS gen2_operating_hours,
    ROUND(avg(hydro_data.gen2_gearbox_temp)::numeric,0) AS gen2_gearbox_temp,
    ROUND(max(hydro_data.gen2_energy_mwh)::numeric,3) AS gen2_energy_mwh,
    ROUND(avg(hydro_data.gen2_torque)::numeric,0) AS gen2_torque,
    ROUND(avg(hydro_data.room_temp)::numeric,2) AS room_temp,
    ROUND(avg(hydro_data.control_panel_temp)::numeric,2) AS control_panel_temp
FROM public.hydro_data
GROUP BY date_trunc('hour',hydro_data.received_at);

CREATE UNIQUE INDEX ON h_hydro_data (received_at);

REFRESH MATERIALIZED VIEW h_hydro_data;

SELECT * FROM h_hydro_data ORDER BY received_at DESC LIMIT 5;

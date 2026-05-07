from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RobustelCellularStatus:
    id: int
    modem_status: str
    current_sim: str
    reg: int
    registration: str
    cell_id: str
    operator: str
    network_type: str
    csq: str
    csq_value: int
    plmn_id: str
    lac: str
    imsi: str
    rsrp_value: int
    modem_model: str
    imei: str
    firmware_version: str
    iccid: str
    phone_num: str
    pci: int
    band: int
    rsrp: str
    rsrq: str
    rsrq_value: int
    sinr: str
    sinr_value: int
    link_uptime: str


@dataclass(frozen=True)
class RobustelSpeedtestResult:
    download_mbps: float
    upload_mbps: float


@dataclass(frozen=True)
class RobustelSimInfo:
    iccid_number: str
    operator: str


@dataclass(frozen=True)
class RobustelSnapshot:
    cellular: RobustelCellularStatus
    speedtest: RobustelSpeedtestResult
    sim: RobustelSimInfo

    def to_dict(self) -> dict:
        return asdict(self)


class FakeRobustelClient:
    """Fake client shaped around the CLI responses we expect from Robustel routers."""

    def get_snapshot(self, store: str | None = None) -> RobustelSnapshot:
        return RobustelSnapshot(
            cellular=RobustelCellularStatus(
                id=1,
                modem_status="Ready",
                current_sim="SIM1",
                reg=5,
                registration="Registered, roaming",
                cell_id="07A4609",
                operator="EE *",
                network_type="LTE",
                csq="22 (-69dBm)",
                csq_value=22,
                plmn_id="23430",
                lac="5F8D",
                imsi="278773004561291",
                rsrp_value=-101,
                modem_model="EC25-EC",
                imei="865828067339828",
                firmware_version="EC25ECGAR06A16M1G_20.300.20.300",
                iccid="8935711001098291187F",
                phone_num="",
                pci=107,
                band=7,
                rsrp="-101 dBm",
                rsrq="-12 dB",
                rsrq_value=-12,
                sinr="6 dB",
                sinr_value=6,
                link_uptime="5 days, 05:18:29",
            ),
            speedtest=RobustelSpeedtestResult(download_mbps=18.0, upload_mbps=6.1),
            sim=RobustelSimInfo(iccid_number="8900000001098291021F", operator="Smooth/Pelion Melita"),
        )


def evaluate_signal(snapshot: RobustelSnapshot) -> tuple[str, str, str]:
    cellular = snapshot.cellular
    speedtest = snapshot.speedtest
    issues: list[str] = []

    if cellular.modem_status.lower() != "ready":
        issues.append(f"modem is {cellular.modem_status}")
    if cellular.reg != 5:
        issues.append(f"registration code is {cellular.reg}")
    if cellular.network_type.upper() != "LTE":
        issues.append(f"network type is {cellular.network_type}")
    if cellular.rsrp_value <= -110:
        issues.append(f"weak RSRP {cellular.rsrp}")
    elif cellular.rsrp_value <= -100:
        issues.append(f"borderline RSRP {cellular.rsrp}")
    if cellular.sinr_value < 5:
        issues.append(f"poor SINR {cellular.sinr}")
    elif cellular.sinr_value < 10:
        issues.append(f"borderline SINR {cellular.sinr}")
    if speedtest.download_mbps < 5 or speedtest.upload_mbps < 1:
        issues.append(f"low throughput {speedtest.download_mbps}Mbps down / {speedtest.upload_mbps}Mbps up")

    if not issues:
        return "ok", "info", "Robustel router is registered on LTE and throughput is healthy."

    severity = "critical" if any("modem" in issue or "low throughput" in issue or "weak RSRP" in issue for issue in issues) else "warning"
    return "needs_review", severity, f"Robustel router needs review: {', '.join(issues)}."

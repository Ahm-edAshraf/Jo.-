"""Slash commands for audio filters (bassboost, nightcore, reset)."""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
import mafic
from mafic import Filter
from mafic.filter import EQBand, Equalizer, Timescale

if TYPE_CHECKING:
    from bot import MusicBot


def _get_player(interaction: discord.Interaction) -> mafic.Player | None:
    if interaction.guild is None:
        return None
    vc = interaction.guild.voice_client
    if vc is None or not isinstance(vc, mafic.Player):
        return None
    return vc


# Bass boost: boost lower EQ bands (0–5). Lavalink bands 0–14, 0 is lowest.
BASSBOOST_BANDS = [
    (0, 0.2),
    (1, 0.15),
    (2, 0.1),
    (3, 0.05),
    (4, 0.0),
    (5, -0.05),
]


class FiltersCog(discord.app_commands.Group):
    """Audio filter commands."""

    def __init__(self, bot: MusicBot) -> None:
        super().__init__(name="filter", description="Apply or reset audio filters")
        self.bot = bot

    @app_commands.command(name="bassboost", description="Apply bass boost")
    async def bassboost(self, interaction: discord.Interaction) -> None:
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            await interaction.response.send_message(
                "Not connected to voice.", ephemeral=True
            )
            return
        if await vc.has_filter("bassboost"):
            await vc.remove_filter("bassboost", fast_apply=True)
        eq = Equalizer(bands=[EQBand(band=b, gain=g) for b, g in BASSBOOST_BANDS])
        flt = Filter(equalizer=eq)
        await vc.add_filter(flt, label="bassboost", fast_apply=True)
        await interaction.response.send_message("Bass boost applied.")

    @app_commands.command(name="nightcore", description="Apply nightcore (speed + pitch)")
    async def nightcore(self, interaction: discord.Interaction) -> None:
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            await interaction.response.send_message(
                "Not connected to voice.", ephemeral=True
            )
            return
        if await vc.has_filter("nightcore"):
            await vc.remove_filter("nightcore", fast_apply=True)
        ts = Timescale(speed=1.2, pitch=1.2)
        flt = Filter(timescale=ts)
        await vc.add_filter(flt, label="nightcore", fast_apply=True)
        await interaction.response.send_message("Nightcore applied.")

    @app_commands.command(name="reset", description="Remove all filters")
    async def reset(self, interaction: discord.Interaction) -> None:
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            await interaction.response.send_message(
                "Not connected to voice.", ephemeral=True
            )
            return
        await vc.clear_filters(fast_apply=True)
        await interaction.response.send_message("Filters reset.")

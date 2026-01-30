"""Slash commands for audio filters (bassboost, nightcore, reset)."""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
import mafic
from mafic import Filter
from mafic.filter import EQBand, Equalizer, Timescale

from embed_styles import (
    Icons, build_filter_embed, build_error_embed, build_success_embed
)

if TYPE_CHECKING:
    from bot import MusicBot


def _get_player(interaction: discord.Interaction) -> mafic.Player | None:
    """Get the Mafic player for the interaction's guild."""
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

    @app_commands.command(name="bassboost", description="Apply bass boost filter")
    async def bassboost(self, interaction: discord.Interaction) -> None:
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            embed = build_error_embed(
                "Not Connected",
                "Bot is not in a voice channel."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if already applied and remove first
        if await vc.has_filter("bassboost"):
            await vc.remove_filter("bassboost", fast_apply=True)
        
        # Apply bass boost
        eq = Equalizer(bands=[EQBand(band=b, gain=g) for b, g in BASSBOOST_BANDS])
        flt = Filter(equalizer=eq)
        await vc.add_filter(flt, label="bassboost", fast_apply=True)
        
        embed = build_filter_embed("Bass Boost 🔊", applied=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nightcore", description="Apply nightcore filter (speed + pitch)")
    async def nightcore(self, interaction: discord.Interaction) -> None:
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            embed = build_error_embed(
                "Not Connected",
                "Bot is not in a voice channel."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if already applied and remove first
        if await vc.has_filter("nightcore"):
            await vc.remove_filter("nightcore", fast_apply=True)
        
        # Apply nightcore
        ts = Timescale(speed=1.2, pitch=1.2)
        flt = Filter(timescale=ts)
        await vc.add_filter(flt, label="nightcore", fast_apply=True)
        
        embed = build_filter_embed("Nightcore ⚡", applied=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="slowreverb", description="Apply slow + reverb filter (slowed)")
    async def slowreverb(self, interaction: discord.Interaction) -> None:
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            embed = build_error_embed(
                "Not Connected",
                "Bot is not in a voice channel."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if already applied and remove first
        if await vc.has_filter("slowreverb"):
            await vc.remove_filter("slowreverb", fast_apply=True)
        
        # Apply slowed effect
        ts = Timescale(speed=0.85, pitch=0.9)
        flt = Filter(timescale=ts)
        await vc.add_filter(flt, label="slowreverb", fast_apply=True)
        
        embed = build_filter_embed("Slow + Reverb 🌙", applied=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="vaporwave", description="Apply vaporwave filter (aesthetic)")
    async def vaporwave(self, interaction: discord.Interaction) -> None:
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            embed = build_error_embed(
                "Not Connected",
                "Bot is not in a voice channel."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if already applied and remove first
        if await vc.has_filter("vaporwave"):
            await vc.remove_filter("vaporwave", fast_apply=True)
        
        # Apply vaporwave (slowed + pitch shifted)
        ts = Timescale(speed=0.8, pitch=0.8)
        flt = Filter(timescale=ts)
        await vc.add_filter(flt, label="vaporwave", fast_apply=True)
        
        embed = build_filter_embed("Vaporwave 🌴", applied=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reset", description="Remove all audio filters")
    async def reset(self, interaction: discord.Interaction) -> None:
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            embed = build_error_embed(
                "Not Connected",
                "Bot is not in a voice channel."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await vc.clear_filters(fast_apply=True)
        
        embed = build_success_embed(
            "Filters Reset",
            f"{Icons.SUCCESS} All audio filters have been removed."
        )
        await interaction.response.send_message(embed=embed)

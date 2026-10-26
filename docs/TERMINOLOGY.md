<!-- SPDX-License-Identifier: MIT -->
# Terminology

> **Audience:** Maintainers and contributors
> **Purpose:** Terminology reference for Energy Usage.
> **Status:** Current documentation baseline
> **Release:** 0.1.0
> **Last Updated:** 2026-10-23

## CCA

Community Choice Aggregator. A governmental entity that procures electricity
on behalf of participating residents and businesses.

## CPUC

California Public Utilities Commission.

## DER

Distributed Energy Resources. Small-scale decentralized generation, storage,
or flexible energy resources located near the point of consumption.

Examples include rooftop solar, batteries, and electric vehicles.

## EDC / DISCO

Electric Distribution Company / Distribution Company.

The organization that owns or operates the local distribution infrastructure
used to deliver electricity to customers.

## DMD

Green Button Download My Data.

## CMD

Green Button Connect My Data.

## ESPI

Energy Services Provider Interface. The data model and interfaces underlying
Green Button.

## UsagePoint

An ESPI logical location where consumption or production is measured or
estimated.

## MeterReading

An ESPI resource grouping readings associated with a measurement.

## ReadingType

Metadata describing the characteristics of readings associated with a
MeterReading.

## IntervalBlock

An ESPI collection of interval readings.

## IntervalReading

An individual interval measurement.

## Import

Energy delivered from an electric grid to a customer.

## Export

Energy delivered from a customer or DER to an electric grid.

## Net

A measurement representing the difference between energy import and export.

## Usage date range

The start and end dates or times selected when viewing or retrieving
consumption history. The start is included and the end is excluded.
The interface shows dates in the Home Assistant configured local time zone.
Internal requests use UTC timestamps; customers do not enter UTC offsets.

Backend code may call a UTC request segment a `window`, but user-facing
text should always say **usage date range**. A date range is not inherently
measured in days: it may cover hours, days, or longer history. The current
backend limits each individual request to 31 days, and the integration
combines multiple requests for longer date ranges.

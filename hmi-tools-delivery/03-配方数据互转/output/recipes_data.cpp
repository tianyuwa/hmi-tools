#ifndef RECIPES_DATA_H
#define RECIPES_DATA_H

// Recipe Data Structure (auto-generated)
// Generated: 2026-05-06 21:17

#include <QString>
#include <QVariantMap>

struct RecipeData {
    QString name;
    QVariantMap params;
};

static const RecipeData g_recipes[] = {
    {"Recipe_001", {
        {"Temp", 180},
        {"Pressure", 2.5},
        {"Speed", 1200},
        {"Time", 30},
        {"Coolant", "On"},
        {"Mode", "Auto"},
    }},
    {"Recipe_002", {
        {"Temp", 220},
        {"Pressure", 3.0},
        {"Speed", 800},
        {"Time", 45},
        {"Coolant", "Off"},
        {"Mode", "Manual"},
    }},
    {"Recipe_003", {
        {"Temp", 150},
        {"Pressure", 1.8},
        {"Speed", 1500},
        {"Time", 20},
        {"Coolant", "On"},
        {"Mode", "Auto"},
    }},
};

#endif // RECIPES_DATA_H

#ifndef Source_h
#define Source_h

#include <QtCore>
#include "Path.h"

struct Source {
    GccArguments args;
    quint64 lastModified;
    Hash<Path, quint64> dependencies;
    bool fromUnsavedFile;
};

static inline QDebug operator<<(QDebug dbg, const Source &s)
{
    dbg << s.args << s.lastModified << s.dependencies << s.fromUnsavedFile;
    return dbg;
}

static inline QDataStream &operator<<(QDataStream &ds, const Source &s)
{
    ds << s.args << s.lastModified;
    ds << s.fromUnsavedFile;
    if (!s.fromUnsavedFile)
        ds << s.dependencies;
    return ds;
}

static inline QDataStream &operator>>(QDataStream &ds, Source &s)
{
    ds >> s.args >> s.lastModified >> s.fromUnsavedFile;

    if (!s.fromUnsavedFile)
        ds >> s.dependencies;
    return ds;
}

#endif

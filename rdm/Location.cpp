#include "Location.h"
#include "Server.h"
#include "Database.h"

Hash<Path, quint32> Location::sPathsToIds;
Hash<quint32, Path> Location::sIdsToPaths;
quint32 Location::sLastId = 0;
QReadWriteLock Location::sLock;

void Location::writeToDB(const Path &path, quint32 id)
{
    // printf("Writing a value here %s %d\n", path.constData(), id);
    Server::instance()->db(Server::FileIds, ScopedDB::Write)->setValue<quint32>(path, id);
}

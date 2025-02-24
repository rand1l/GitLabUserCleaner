import asyncio
import aiohttp
import os
import sys

# Получение переменных окружения
GITLAB_URL = os.getenv('GITLAB_URL')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')

# Проверка наличия необходимых переменных окружения
if not GITLAB_URL or not GITLAB_TOKEN:
    print("Ошибка: Переменные окружения GITLAB_URL и GITLAB_TOKEN должны быть установлены.")
    sys.exit(1)

headers = {
    'Private-Token': GITLAB_TOKEN
}


async def fetch(session, url, method='GET', data=None):
    """функция для выполнения HTTP запроса."""
    async with session.request(method, url, headers=headers, json=data) as response:
        if response.status != 200:
            print(f"Ошибка при выполнении запроса: {response.status} - {url}")
            return []
        return await response.json()


async def delete_user_from_group(session, group_id, user_id, group_name, user_info):
    """функция для удаления пользователя из группы."""
    url = f'{GITLAB_URL}/api/v4/groups/{group_id}/members/{user_id}'
    async with session.delete(url, headers=headers) as response:
        if response.status == 204:
            print(
                f"Пользователь {user_info['name']} (Username: {user_info['username']}, Email: {user_info['email']}, ID: {user_id}) успешно удален из группы '{group_name}' (ID: {group_id}).")
        else:
            print(
                f"Ошибка при удалении пользователя {user_info['name']} (Username: {user_info['username']}, Email: {user_info['email']}, ID: {user_id}) из группы '{group_name}' (ID: {group_id}): {response.status}")


async def delete_user_from_project(session, project_id, user_id, project_name, user_info):
    """функция для удаления пользователя из проекта."""
    url = f'{GITLAB_URL}/api/v4/projects/{project_id}/members/{user_id}'
    async with session.delete(url, headers=headers) as response:
        if response.status == 204:
            print(
                f"Пользователь {user_info['name']} (Username: {user_info['username']}, Email: {user_info['email']}, ID: {user_id}) успешно удален из проекта '{project_name}' (ID: {project_id}).")
        else:
            print(
                f"Ошибка при удалении пользователя {user_info['name']} (Username: {user_info['username']}, Email: {user_info['email']}, ID: {user_id}) из проекта '{project_name}' (ID: {project_id}): {response.status}")


async def get_all_users(session):
    """функция для получения всех пользователей GitLab."""
    users = []
    page = 1
    while True:
        url = f'{GITLAB_URL}/api/v4/users?page={page}&per_page=100'
        current_page_users = await fetch(session, url)
        if not current_page_users:
            break
        users.extend(current_page_users)
        page += 1
    return users


async def find_blocked_or_banned_users(users, state):
    """Функция для фильтрации пользователей по состоянию (blocked или banned)."""
    filtered_users = {
        user['id']: {'name': user['name'], 'username': user['username'], 'email': user['email'], 'groups': [],
                     'blocked_projects': [], 'active_projects': []}
        for user in users if user['state'] == state}
    return filtered_users


async def get_all_groups(session):
    """функция для получения всех групп."""
    groups = []
    page = 1
    while True:
        url = f'{GITLAB_URL}/api/v4/groups?page={page}&per_page=100'
        current_page_groups = await fetch(session, url)
        if not current_page_groups:
            break
        groups.extend(current_page_groups)
        page += 1
    return groups


async def get_all_projects(session):
    """функция для получения всех проектов."""
    projects = []
    page = 1
    while True:
        url = f'{GITLAB_URL}/api/v4/projects?page={page}&per_page=100'
        current_page_projects = await fetch(session, url)
        if not current_page_projects:
            break
        projects.extend(current_page_projects)
        page += 1
    return projects


async def find_users_in_group(session, group, user_data):
    """функция для нахождения пользователей в группе и добавления информации о группах и проектах."""
    page = 1
    group_name = group['name']
    while True:
        url = f'{GITLAB_URL}/api/v4/groups/{group["id"]}/members?page={page}&per_page=100'
        members = await fetch(session, url)
        if not members:
            break
        for member in members:
            if member['id'] in user_data:
                user_data[member['id']]['groups'].append((group['id'], group_name))
        page += 1


async def find_users_in_project(session, project, user_data):
    """функция для нахождения пользователей в проекте и добавления информации о группах и проектах."""
    page = 1
    project_name = project['name']
    while True:
        url = f'{GITLAB_URL}/api/v4/projects/{project["id"]}/members?page={page}&per_page=100'
        members = await fetch(session, url)
        if not members:
            break
        for member in members:
            if member['id'] in user_data:
                user_data[member['id']]['blocked_projects'].append((project['id'], project_name))
            else:
                for user in user_data.values():
                    if user['username'] == member['username']:
                        user['active_projects'].append((project['id'], project_name))
        page += 1


async def main():
    async with aiohttp.ClientSession() as session:
        # Получение всех пользователей
        all_users = await get_all_users(session)
        print(f'Всего пользователей найдено: {len(all_users)}')

        # Фильтрация заблокированных пользователей
        blocked_users = await find_blocked_or_banned_users(all_users, 'blocked')
        print(f'Заблокированных пользователей найдено: {len(blocked_users)}')

        # Фильтрация забаненных пользователей
        banned_users = await find_blocked_or_banned_users(all_users, 'banned')
        print(f'Забаненных пользователей найдено: {len(banned_users)}')

        groups = await get_all_groups(session)
        print(f'Всего групп найдено: {len(groups)}')

        projects = await get_all_projects(session)
        print(f'Всего проектов найдено: {len(projects)}')

        # Проверка заблокированных пользователей в группах и проектах
        tasks = [find_users_in_group(session, group, blocked_users) for group in groups]
        await asyncio.gather(*tasks)

        tasks = [find_users_in_project(session, project, blocked_users) for project in projects]
        await asyncio.gather(*tasks)

        # Проверка забаненных пользователей в группах и проектах
        tasks = [find_users_in_group(session, group, banned_users) for group in groups]
        await asyncio.gather(*tasks)

        tasks = [find_users_in_project(session, project, banned_users) for project in projects]
        await asyncio.gather(*tasks)

        # Удаление заблокированных пользователей из групп и проектов
        print("\nУдаление заблокированных пользователей...")
        for user_id, user_info in blocked_users.items():
            if user_info['groups']:
                for group_id, group_name in user_info['groups']:
                    await delete_user_from_group(session, group_id, user_id, group_name, user_info)
            if user_info['blocked_projects']:
                for project_id, project_name in user_info['blocked_projects']:
                    await delete_user_from_project(session, project_id, user_id, project_name, user_info)

        # Удаление забаненных пользователей из групп и проектов
        print("\nУдаление забаненных пользователей...")
        for user_id, user_info in banned_users.items():
            if user_info['groups']:
                for group_id, group_name in user_info['groups']:
                    await delete_user_from_group(session, group_id, user_id, group_name, user_info)
            if user_info['blocked_projects']:
                for project_id, project_name in user_info['blocked_projects']:
                    await delete_user_from_project(session, project_id, user_id, project_name, user_info)


if __name__ == "__main__":
    asyncio.run(main())

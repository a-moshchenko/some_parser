import asyncio

import pandas as pd
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from config import HEADERS, DOMAIN, PATH_TO_DATA
from data_getter import DataGetter

logger.add('parser.log', level='DEBUG', rotation='00:00', retention=1)


class Parser:

    @classmethod
    async def get_all_pages(cls):
        tasks = []
        pages = []
        loop = asyncio.get_event_loop()
        page = await DataGetter.get_request('https://theresanaiforthat.com/alphabetical/#switch', headers=HEADERS)
        soup = BeautifulSoup(page, 'lxml')
        links = [i['href'] for i in soup.find_all('a', attrs={'class': 'ai_link new_tab'})]
        for link in tqdm(links):
            tasks.append(loop.create_task(DataGetter.get_request(f'{DOMAIN}{link}', headers=HEADERS)))
            if len(tasks) > 49:
                pages += await asyncio.gather(*tasks)
                tasks = []
        pages += await asyncio.gather(*tasks)
        return pages

    @classmethod
    async def collect_info(cls, pages: list[str]) -> list:
        loop = asyncio.get_event_loop()
        collected_data = []
        tasks = []
        for page in tqdm(pages):
            tasks.append(loop.create_task(cls.get_page_info(page)))
            if len(tasks) > 199:
                collected_data += await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
        collected_data += await asyncio.gather(*tasks, return_exceptions=True)
        return collected_data

    @classmethod
    async def run(cls):
        while True:
            try:
                pages = await cls.get_all_pages()
                data = [i for i in await cls.collect_info(pages) if i is not None]
                logger.success('Saving data ...')
                df = pd.DataFrame(data=data)
                df.to_excel(PATH_TO_DATA / "result.xlsx", index=False)
                logger.success("Done ...")
                await asyncio.sleep(60 * 60 * 24)
            except Exception as e:
                logger.exception(e)

    @classmethod
    async def get_page_info(cls, page: str) -> dict | None:
        data = {}
        soup = BeautifulSoup(page, 'lxml')
        rank_div = soup.find('div', id='rank')
        price = rank_div.find('span', class_='tag price')
        all_tags = [i.text for i in rank_div.find_all('span', class_='tag')]
        image_url = soup.find('img', class_='ai_image')['src']
        image_name = cls.get_image_name(image_url)
        if not_available := soup.find('div', class_='visit_website'):
            if not_available.text.strip() == 'This AI tool is no longer available.':
                logger.warning(f"{soup.find('h1').find_all('div')[-1].text}  This AI tool is no longer available.")
                return
        data['name'] = soup.find('h1').find_all('div')[-1].text
        data['category'] = soup.find('span', class_='rank_task_name').text
        data['tags'] = ','.join(all_tags[:-1]) if price else ','.join(all_tags)
        data['price'] = price.text if price else None
        if description := soup.find('div', class_='description'):
            data['description'] = '. '.join([i.text.strip() for i in description.find_all('p')])
        else:
            data['description'] = None
            logger.warning(f"{data['name']} has no description")
        data['home_page'] = soup.find('div', class_='visit_website').find('a')['href'].split('?')[0]
        data['image'] = image_name
        if image_name:
            await cls._get_image(image_url, image_name)
        else:
            logger.warning(f"{data['name']} without image")
        return data

    @classmethod
    async def _get_image(cls, image_url: str, image_name: str):
        image_data = await DataGetter.get_request(image_url, headers=HEADERS, only_bytes=True)
        file_path = PATH_TO_DATA / 'images' / image_name
        with open(file_path, 'wb') as image_file:
            image_file.write(image_data)

    @staticmethod
    def save_data_to_excel(data: list[dict]):
        ...

    @staticmethod
    def get_image_name(image_url: str) -> str | None:
        name = image_url.split('/')[-1]
        if name == 'ai-placeholder.png':
            return
        return image_url.split('/')[-1]

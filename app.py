import os
import tornado.ioloop
import tornado.web
import tornado.escape
import motor.motor_tornado
from bson import ObjectId


client = motor.motor_tornado.MotorClient(os.environ["MONGODB_URL"])
db = client.college


class MainHandler(tornado.web.RequestHandler):
    async def get(self, **kwargs):
        if (student_id := kwargs.get("student_id")) is not None:
            if (
                student := await self.settings["db"]["students"].find_one(
                    {"_id": student_id}
                )
            ) is not None:
                return self.write(student)
            else:
                raise tornado.web.HTTPError(404)
        else:
            students = await self.settings["db"]["students"].find().to_list(1000)
            return self.write({"students": students})

    async def post(self):
        student = tornado.escape.json_decode(self.request.body)
        student["_id"] = str(ObjectId())

        new_student = await self.settings["db"]["students"].insert_one(student)
        created_student = await self.settings["db"]["students"].find_one(
            {"_id": new_student.inserted_id}
        )

        self.set_status(201)
        return self.write(created_student)

    async def put(self, **kwargs):
        if (student_id := kwargs.get("student_id")) is not None:
            student = tornado.escape.json_decode(self.request.body)
            await self.settings["db"]["students"].update_one(
                {"_id": student_id}, {"$set": student}
            )

            if (
                updated_student := await self.settings["db"]["students"].find_one(
                    {"_id": student_id}
                )
            ) is not None:
                return self.write(updated_student)

        raise tornado.web.HTTPError(404)

    async def delete(self, **kwargs):
        if (student_id := kwargs.get("student_id")) is not None:
            delete_result = await db["students"].delete_one({"_id": student_id})

            if delete_result.deleted_count == 1:
                self.set_status(204)
                return self.finish()

        raise tornado.web.HTTPError(404)


app = tornado.web.Application(
    [
        (r"/", MainHandler),
        (r"/(?P<student_id>\w+)", MainHandler),
    ],
    db=db,
)

if __name__ == "__main__":
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()
